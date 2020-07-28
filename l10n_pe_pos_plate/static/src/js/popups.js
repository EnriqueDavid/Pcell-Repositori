odoo.define('l10n_pe_pos_plate.popups', function (require) {
"use strict";
var models = require('point_of_sale.models');
var rpc = require('web.rpc');
var PopupWidget = require('point_of_sale.popups');
var gui = require('point_of_sale.gui');

var PlateInfoWidget = PopupWidget.extend({
    template: 'PlateInfoWidget',
    show: function(options){
        options = options || {};
        this._super(options);
        this.renderElement();
        var self = this
        $('.apply_product_number_button').click(function(event){
        	 var pe_license_plate = $(".numb_detail").val()
             var selectedOrder = self.pos.get_order();
             var number = selectedOrder.get_pe_license_plate()
             pe_license_plate = pe_license_plate || number;
        	 var line = selectedOrder.get_orderlines();
             if (pe_license_plate){
	        	 if (!number){
                    selectedOrder.set_pe_license_plate(pe_license_plate)
                 }
	        	 _.each(selectedOrder.get_orderlines(), function(line_prod){
		         if(line_prod.id === selectedOrder.get_selected_orderline().id){
		        	 line_prod.pe_license_plate = pe_license_plate
		        	 line_prod.product.pe_license_plate = pe_license_plate
		        	 self.trigger('change');
		             }
		            });
	        	 //console.log("line no is.........................",selectedOrder.get_selected_orderline().number)
	        	 self.gui.close_popup();
        	 }
             else {
                
             }
        	
        });
    },
});
gui.define_popup({name:'plate-check', widget:PlateInfoWidget});

var ConfirmPlatePopupWidget = PopupWidget.extend({
    template: 'ConfirmPlatePopupWidget',
    show: function(options){
    options = options || {};
    this._super(options);
    this.renderElement();
    },
});
gui.define_popup({name:'plate_confirm', widget: ConfirmPlatePopupWidget});

return PopupWidget;
});