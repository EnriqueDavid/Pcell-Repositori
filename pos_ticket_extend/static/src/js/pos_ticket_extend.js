odoo.define('pos_ticket_extend.pos_ticket_extend', function (require) {
"use strict";

var models = require('point_of_sale.models');

models.load_fields("res.company", ["street"]);

});
