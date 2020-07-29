odoo.define('pos_journal_sequence.pos_journal_sequence', function (require) {
    "use strict";

    var models = require('point_of_sale.models');
    var screens = require('point_of_sale.screens');
    var PosDB = require('point_of_sale.DB');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var concurrency = require('web.concurrency');
    var QWeb = core.qweb;

    var _t = core._t;

    var PosModelSuper = models.PosModel;
    var PosDBSuper = PosDB;
    var OrderSuper = models.Order;
    var Mutex = concurrency.Mutex;

    models.load_fields('pos.config', ['invoice_journal_ids']);

    PosDB = PosDB.extend({
        init: function (options) {
            this.journal_by_id = {};
            this.sequence_by_id = {};
            this.journal_sequence_by_id = {};
            //this.invoice_numbers=[];
            return PosDBSuper.prototype.init.apply(this, arguments);
        },
        add_invoice_numbers: function (number) {
            if (number) {
                var invoice_numbers = this.load('invoice_numbers') || [];
                invoice_numbers.push(number);
                this.save('invoice_numbers', invoice_numbers || null);
            }
        },
        get_invoice_numbers: function () {
            return this.load('invoice_numbers') || [];
        },
        add_journals: function (journals) {
            if (!journals instanceof Array) {
                journals = [journals];
            }
            for (var i = 0, len = journals.length; i < len; i++) {
                this.journal_by_id[journals[i].id] = journals[i];
                this.journal_sequence_by_id[journals[i].id] = journals[i].sequence_id[0];
            }
        },
        add_sequences: function (sequences) {
            if (!sequences instanceof Array) {
                sequences = [sequences];
            }
            for (var i = 0, len = sequences.length; i < len; i++) {
                this.sequence_by_id[sequences[i].id] = sequences[i];
            }
        },
        get_journal_sequence_id: function (journal_id) {
            var sequence_id = this.journal_sequence_by_id[journal_id]
            return this.sequence_by_id[sequence_id] || {};
        },
        get_journal_id: function (journal_id) {
            return this.journal_by_id[journal_id];
        },
        set_sequence_next: function (id, number_increment) {
            var sequences = this.load('sequences') || {};
            sequences[id] = number_increment + 1;
            this.save('sequences', sequences || null);
        },
        get_sequence_next: function (journal_id) {
            var sequence_id = this.journal_sequence_by_id[journal_id];

            var sequences = this.load('sequences') || {};
            if (sequences[sequence_id]) {
                if (this.sequence_by_id[sequence_id].all_number_increment > sequences[sequence_id]) {
                    return this.sequence_by_id[sequence_id].all_number_increment;
                }
                else {
                    return sequences[sequence_id];
                }
            }
            else {
                return this.sequence_by_id[sequence_id].all_number_increment;
            }
        },
    });

    models.load_models(
        [{
            model: 'account.journal',
            fields: [],
            domain: function (self) { return [['id', 'in', self.config.invoice_journal_ids]]; },
            loaded: function (self, journals) {
                var sequence_ids = [];
                for (var i = 0, len = journals.length; i < len; i++) {
                    sequence_ids.push(journals[i].sequence_id[0]);
                }
                self.journal_ids = journals;
                self.sequence_ids = sequence_ids;
                self.db.add_journals(journals);
            },
        },
        {
            model: 'ir.sequence',
            fields: ['id', 'interpolated_prefix', 'interpolated_suffix', 'padding', 'all_number_increment'],
            domain: function (self) { return [['id', 'in', self.sequence_ids]]; },
            loaded: function (self, sequences) {
                self.db.add_sequences(sequences);
            },
        }]
    );

    models.PosModel = models.PosModel.extend({
        initialize: function (session, attributes) {
            var res = PosModelSuper.prototype.initialize.apply(this, arguments);
            this.db = new PosDB();
            this.mutex = new Mutex();                 // a local database used to search trough products and categories & store pending orders
            return res;
        },
        generate_order_sync_number: function (journal_id) {
            self = this;
            var sequence = this.db.get_journal_sequence_id(journal_id);
            var loading = $(QWeb.render('TabConnecting', {}));
            $.blockUI({
                message: loading.html(),
                css: { backgroundColor: '#f00', color: '#fff' }
            });
            var sequence_promise = new Promise(function (resolvedone, rejectdone) {
                self.mutex.exec(function () {
                    return rpc.query({
                        model: 'ir.sequence',
                        method: 'pos_get_sync_number',
                        args: [sequence.id, self.db.get_sequence_next(journal_id)],
                    }).then(function (result) {
                        $.unblockUI();
                        resolvedone(result)
                        console.log('success to get sequence number', result.number);
                    }).catch(function (result) {
                        $.unblockUI();
                        var numbers = self.generate_order_number(journal_id);
                        resolvedone(numbers)
                        console.log('Failed to get sequence number');
                    })
                })
            })
            return sequence_promise
        },
        generate_order_number: function (journal_id) {
            var sequence = this.db.get_journal_sequence_id(journal_id);
            var num = "%0" + sequence.padding + "d";
            var prefix = sequence.interpolated_prefix || "";
            var suffix = sequence.interpolated_suffix || "";
            var increment = this.db.get_sequence_next(journal_id);
            var number = prefix + num.sprintf(parseInt(increment)) + suffix;
            return { 'number': number, 'invoice_sequence_number': increment };
        },
        get_order_number: function (journal_id) {
            var self = this;
            var sequence_differed = jQuery.Deferred();
            if (this.config.is_sync) {
                var sync_number = this.generate_order_sync_number(journal_id);
                sync_number.then(function (numbers) {
                    if (self.db.get_invoice_numbers().indexOf(numbers.number) != -1) {
                        numbers = self.get_order_number(journal_id);
                    }
                    sequence_differed.resolve(numbers)
                });
            }
            else {
                var numbers = this.generate_order_number(journal_id);
                if (this.db.get_invoice_numbers().indexOf(numbers.number) != -1) {
                    numbers = this.get_order_number(journal_id);
                    var new_sequence = this.db.get_journal_sequence_id(journal_id);
                    this.db.set_sequence_next(new_sequence.id, numbers.invoice_sequence_number);
                }
                sequence_differed.resolve(numbers)
            }
            return sequence_differed;
        },
        set_sequence: function (journal_id, number, number_increment) {
            var sequence = this.db.get_journal_sequence_id(journal_id);
            this.db.set_sequence_next(sequence.id, number_increment);
            this.db.add_invoice_numbers(number);

        },
    });

    models.Order = models.Order.extend({
        initialize: function (attributes, options) {
            var res = OrderSuper.prototype.initialize.apply(this, arguments);
            this.number = false;
            this.journal_id = false;
            this.invoice_sequence_number = 0;
            this.sequence_set = false;
            this.date_invoice = false;
            return res;
        },
        set_sale_journal: function (journal_id) {
            this.assert_editable();
            this.journal_id = journal_id;
        },
        get_sale_journal: function () {
            return this.journal_id;
        },
        export_as_JSON: function () {
            var res = OrderSuper.prototype.export_as_JSON.apply(this, arguments);
            res['invoice_journal'] = this.journal_id;
            res['number'] = this.number;
            res['invoice_sequence_number'] = this.invoice_sequence_number;
            res['date_invoice'] = moment(new Date().getTime()).format('YYYY/MM/DD');
            return res;
        },
        set_number: function (number) {
            this.assert_editable();
            this.number = number;
        },
        get_number: function () {
            return this.number;
        },
        get_sequence_set: function () {
            return this.sequence_set;
        },
        set_sequence_set: function (sequence_set) {
            this.assert_editable();
            this.sequence_set = sequence_set;
        },
        set_sequence_number: function (number) {
            this.assert_editable();
            this.invoice_sequence_number = number;
        },
        get_sequence_number: function () {
            return this.invoice_sequence_number;
        },
    });

    screens.PaymentScreenWidget.include({
        renderElement: function () {
            var self = this;
            this._super();
            var sale_journals = this.render_sale_journals();
            sale_journals.appendTo(this.$('.payment-buttons'));
            this.$('.js_sale_journal').click(function () {
                self.click_sale_journals($(this).data('id'));
            });
        },
        render_sale_journals: function () {
            var self = this;
            var sale_journals = $(QWeb.render('SaleInvoiceJournal', { widget: this }));
            return sale_journals;
        },
        click_sale_journals: function (journal_id) {
            var order = this.pos.get_order();
            if (order.get_sale_journal() != journal_id) {
                order.set_sale_journal(journal_id);
                this.$('.js_sale_journal').removeClass('highlight');
                this.$('div[data-id="' + journal_id + '"]').addClass('highlight');
            }
            else {
                order.set_sale_journal(false);
                this.$('.js_sale_journal').removeClass('highlight');
            }

        },
        validate_journal_invoice: function () {
            var res = false;
            var order = this.pos.get_order();
            if (!order.get_client() && this.pos.config.anonymous_id) {
                var new_client = this.pos.db.get_partner_by_id(this.pos.config.anonymous_id[0]);
                if (new_client) {
                    order.fiscal_position = _.find(this.pos.fiscal_positions, function (fp) {
                        return fp.id === new_client.property_account_position_id[0];
                    });
                } else {
                    order.fiscal_position = undefined;
                }
                if (new_client) {
                    order.set_client(new_client);
                }
            }
            if (!order.get_client() && order.get_sale_journal()) {
                this.gui.show_popup('confirm', {
                    'title': _t('An anonymous order cannot be invoiced'),
                    'body': _t('You need to select the customer before you can invoice an order.'),
                    confirm: function () {
                        this.gui.show_screen('clientlist');
                    },
                });
                res = true;
            }
            return res;
        },
        order_is_valid: function (force_validation) {
            var res = this._super(force_validation);
            if (!res) {
                return res;
            }
            if (this.validate_journal_invoice()) {
                return;
            }
            return res;
        },
        finalize_validation: function () {
            var self = this;
            var super_finalize_validation = self._super
            var differed = jQuery.Deferred();
            var order = self.pos.get_order();
            var sync_sequence = self.pos.get_order_number(order.get_sale_journal());
            sync_sequence.done(function (numbers) {
                order.set_number(numbers.number);
                order.set_sequence_number(numbers.invoice_sequence_number);
                if (order.get_number() && !order.get_sale_journal()) {
                    order.set_sequence_set(false);
                    order.set_number(false);
                    order.set_sequence_number(0);
                }
                if (order.get_number() && !order.get_sequence_set()) {
                    order.set_sequence_set(true);
                    self.pos.set_sequence(
                        order.get_sale_journal(), order.get_number(),
                        order.get_sequence_number())
                }
                if (!order.get_number() && order.get_sale_journal()) {
                    differed.reject()
                } else {
                    differed.resolve(self)
                }
            })
            differed.then(function (func_self) {
                super_finalize_validation.call(func_self)
            }).catch(function () {
                self.gui.show_popup('error', _t('Could not get the number'));
            });
        },
    });

});
