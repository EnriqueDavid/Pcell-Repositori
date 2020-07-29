odoo.define('l10n_pe_pos_plate.pos_product_number', function (require) {
"use strict";
var screens = require('point_of_sale.screens');
var models = require('point_of_sale.models');
var PopUpWidget=require('point_of_sale.popups');
var gui = require('point_of_sale.gui');
var core = require('web.core');
var QWeb = core.qweb;
var _t = core._t;

models.load_fields("product.product",['require_plate']);
var _super_order = models.Order.prototype;
models.Order = models.Order.extend({
	initialize: function(attributes,options){
        var res = _super_order.initialize.apply(this, arguments);
        this.pe_license_plate= false;
        return res;
    },
	add_product: function(product, options){
    	_super_order.add_product.apply(this,arguments);
    	var self = this
        if (product.require_plate){
            this.pos.gui.show_popup('plate-check', {
                'title': _t('Plate'),
                'order': this,
            });
        }
	},
    set_pe_license_plate: function(pe_license_plate) {
        this.assert_editable();
        this.pe_license_plate = pe_license_plate;
    },
    get_pe_license_plate: function() {
        return this.pe_license_plate;
    },
});

var _super_order_line = models.Orderline.prototype;

models.Orderline = models.Orderline.extend({
    initialize: function(attributes,options){
        var res = _super_order_line.initialize.apply(this, arguments);
        this.pe_license_plate= false;
        return res;
    },
    export_as_JSON: function() {
        var res = _super_order_line.export_as_JSON.apply(this, arguments);
        res['pe_license_plate'] = this.pe_license_plate
        return res;
    },
});


screens.ActionpadWidget.include({
    template: 'ActionpadWidget',
    init: function(parent, options) {
        var self = this;
        this._super(parent, options);

        this.pos.bind('change:selectedClient', function() {
            self.renderElement();
        });
    },
    renderElement: function() {
        var self = this;
        this._super();
        this.$('.pay').click(function(){
            var order = self.pos.get_order();
            var has_valid_product_lot = _.every(order.orderlines.models, function(line){
                return line.has_valid_product_lot();
            });
            var product_list = [];
            var numb = false
            _.each(order.orderlines.models, function(extra){
            	if(extra.product.require_plate){
                	product_list.push({'product':extra.product,'require_plate':extra.product.require_plate,'numbers':extra.product.number})
                }
            });
            var product_number = false;		
            _.each(product_list,function(no){
            	if(no.numbers === undefined){
            		product_number = true;
            	}
            })
            if(product_number){
        		self.gui.show_popup('plate_confirm',{
                    'title': _t('Plate'),
                    'body':  _t('One or more product(s) required plate.'),
                    confirm: function(){
                        self.gui.show_screen('payment');
                    },
                });
        	}else if(!has_valid_product_lot){
                self.gui.show_popup('confirm',{
                    'title': _t('Empty Serial/Lot Number'),
                    'body':  _t('One or more product(s) required serial/lot number.'),
                    confirm: function(){
                        self.gui.show_screen('payment');
                    },
                });
            }else{
                self.gui.show_screen('payment');
            }
        });
        this.$('.set-customer').click(function(){
            self.gui.show_screen('clientlist');
        });
    }
});
screens.OrderWidget.include({
    template:'OrderWidget',
    
    render_orderline: function(orderline){
        var el_str  = QWeb.render('Orderline',{widget:this, line:orderline}); 
        var el_node = document.createElement('div');
            el_node.innerHTML = _.str.trim(el_str);
            el_node = el_node.childNodes[0];
            el_node.orderline = orderline;
            el_node.addEventListener('click',this.line_click_handler);
        var el_lot_icon = el_node.querySelector('.line-lot-icon');
        if(el_lot_icon){
            el_lot_icon.addEventListener('click', (function() {
                this.show_product_lot(orderline);
            }.bind(this)));
        }
    	
        var el_number_icon = el_node.querySelector('.line-product-number');
        if(el_number_icon){
        	el_number_icon.addEventListener('click', (function() {
                if (orderline.product.require_plate){
                    this.pos.gui.show_popup('plate-check', {
                        'title': _t('Plate'),
                        'order': this,
                    });
                }
            }.bind(this)));
        }
        orderline.node = el_node;
        return el_node;
	},
});


});