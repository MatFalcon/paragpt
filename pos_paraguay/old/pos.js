odoo.define('pos_ruc_heredado', function (require) {
    "use strict";
    var models = require('point_of_sale.models');
    // var screens = require('point_of_sale.screens');
    var utils = require('web.utils');
    var round_pr = utils.round_precision;
    var round_di = utils.round_decimals;
    var field_utils = require('web.field_utils');
    var core = require('web.core');
    var _t = core._t;
    var web_rpc = require('web.rpc');
    var PosDb = require('point_of_sale.DB');
    var SuperPosModel = models.PosModel.prototype;
    var SuperOrder = models.Order.prototype;
    var rpc = require('web.rpc');
    var invoicebutton = require('point_of_sale.InvoiceButton');
    const { useListener } = require('web.custom_hooks');
    const { isConnectionError } = require('point_of_sale.utils');
    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');

    models.load_fields('res.partner',['rucdv','ruc','dv','ci','nombre_fantasia']);
    models.load_fields('res.company',['street']);
    models.load_fields('pos.config',['invoice_report','invoice_report_text','talonario_factura','talonario_nota_credito']);
    // models.load_fields('pos.order',['timbrado','nro_factura']);


    models.load_models([
        {
            model: 'ruc.documentos.timbrados',
            fields: ['name','ultimo_nro_utilizado','fecha_inicio','tipo_documento','fecha_final'],
            loaded : function(self, talonario){
                self.talonario = talonario;

            }
        }
        ]);




    var _super_Order = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function (attributes, options) {
            _super_Order.initialize.apply(this, arguments);
            this.rpc = this.get('rpc');
            this.nro_factura = this.nro_factura || false;;
            this.timbrados = this.timbrados || false;;
            this.inicio_timbrado = this.inicio_timbrado || false;;
            this.fin_timbrado = this.fin_timbrado || false;;
            this.nro_autorizacion_autoimpresor = this.nro_autorizacion_autoimpresor || false;;
            this.ruc_cliente = this.ruc_cliente || false;;
            // console.log('iniciioo');
            // if (this.pos.config.pos_auto_invoice) {//SI ESTA EL TICKET PARA FACTURAR
                //this.currentOrder.set_to_invoice(true);
                 this.to_invoice = true; //SETEAMOS A FACTURAR CON VERDADERO
            // }
        },

        export_as_JSON: function () {
            var json = _super_Order.export_as_JSON.apply(this,arguments);
            json.timbrados = this.timbrados;

            return json
        },
        init_from_JSON: function (json) {
            var res = _super_Order.init_from_JSON.apply(this, arguments);
            this.timbrados = json.timbrados;
            if (json.to_invoice) {

                //this.currentOrder.set_to_invoice(true);
                 this.to_invoice = json.to_invoice;
            }
        },
        // set_timbrado:function(timbrado) {
        //     console.log('entro timbrado')
        //
		// 	this.timbrados = timbrado;
        //     console.log(this);
		// 	// this.trigger('change');
		// 	this.save_to_db();
		// },
        export_for_printing: function(){
            var self = this


            // console.log('props.order');
            // console.log(props.order);
            // console.log('receiptssse')
            // console.log(receipt)

            var timbrado=''
            var inicio_timbrado=''
            var invoice_number=''
            var fin_timbrado=''
            var nro_autorizacion_autoimpresor=''
            var ruc_cliente=''

            if (this.account_move>0){

                rpc.query({
                                        model: 'account.move',
                                        method: 'get_invoice_data',
                                          args:[this.account_move],
                                        }).then(function (result_dict){
                                        // args:[invoice[0], ['nro_factura']]
                                        //     }).then(function(result_dict){

                                                if(result_dict.length){
                                                    invoice_number = result_dict[0];
                                                    timbrado = result_dict[1];
                                                    inicio_timbrado = result_dict[2];
                                                    fin_timbrado = result_dict[3];
                                                    nro_autorizacion_autoimpresor = result_dict[5];
                                                    ruc_cliente = result_dict[6];
                                                }
                                        })

            }
            // console.log('reciiiii');
            // console.log(this);
            // console.log('receipt');
            // console.log(receipt);
            var receipt = SuperOrder.export_for_printing.call(this);
            receipt.invoice_number = invoice_number;
            receipt.timbrado = timbrado;
            receipt.inicio_timbrado = inicio_timbrado;
            receipt.fin_timbrado = fin_timbrado;
            receipt.nro_autorizacion_autoimpresor = nro_autorizacion_autoimpresor;
            receipt.ruc_cliente = ruc_cliente;
            if(self.nro_factura){
                receipt.invoice_number = self.nro_factura;
                receipt.timbrado = self.timbrado;
                receipt.inicio_timbrado = self.inicio_timbrado;
                receipt.fin_timbrado = self.fin_timbrado;
                receipt.ruc_cliente = self.ruc_cliente;

                receipt.nro_autorizacion_autoimpresor = self.nro_autorizacion_autoimpresor;

            }
            receipt.company_street=this.pos.company.street
            return receipt
        }




    });
    models.PosModel = models.PosModel.extend({
        _flush_orders: function(orders, options) {
            var self = this;
            var result, data
            result = data = SuperPosModel._flush_orders.call(this,orders, options)
            _.each(orders,function(order){
                if (order.to_invoice)
                    data.then(function(order_server_id){
                        rpc.query({
                        model: 'pos.order',
                        method: 'read',
                        args:[order_server_id, ['account_move']]
                            }).then(function(result_dict){
                                if(result_dict.length){
                                    let invoice = result_dict[0].account_move;

                                    rpc.query({
                                        model: 'account.move',
                                        method: 'get_invoice_data',
                                          args:[invoice[0]],
                                        }).then(function (result_dict){
                                        // args:[invoice[0], ['nro_factura']]
                                        //     }).then(function(result_dict){
                                                if(result_dict.length){
                                                    self.get_order().nro_factura = result_dict[0];
                                                    self.get_order().timbrado = result_dict[1];
                                                    self.get_order().inicio_timbrado = result_dict[2];
                                                    self.get_order().fin_timbrado = result_dict[3];
                                                    self.get_order().nro_autorizacion_autoimpresor = result_dict[5];
                                                    self.get_order().ruc_cliente = result_dict[6];
                                                    // self.get_order().set_timbrado(result_dict[1]);
                                                }
                                        })

                                    // self.get_order().invoice_number = invoice[1]
                                }
                        })
                        .catch(function(error){
                            return result
                        })
                    })
            })
            return result
        },

    })

// var PosDB = core.Class.extend({
PosDb.include({
    _partner_search_string: function (partner) {
        var str =  partner.name;
        // console.log('bbb');

        this._super(partner);
        if(partner.rucdv){
            str += '|' + partner.rucdv;

        }
        if(partner.ci){
            str += '|' + partner.ci;

        }
        if(partner.nombre_fantasia){
            str += '|' + partner.nombre_fantasia;

        }

        str = '' + partner.id + ':' + str.toString().replace(':','') + '\n';
        return str;

    },

    });

  var _super_Orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        export_for_printing: function(){
            var self = this
            var orderlinere = _super_Orderline.export_for_printing.call(this)
            orderlinere.default_code = this.get_product().default_code;
            return orderlinere
        }

});

   class InvoiceButtonticket extends PosComponent {
        constructor() {
            super(...arguments);
            useListener('click', this._onClick);
        }
        get isAlreadyInvoiced() {
            if (!this.props.order) return false;
            return Boolean(this.props.order.account_move);
        }
        get commandName() {
            if (!this.props.order) {
                return this.env._t('Invoice');
            } else {
                return this.isAlreadyInvoiced
                    ? this.env._t('Reprint Invoice')
                    : this.props.order.isFromClosedSession
                    ? this.env._t('Cannot Invoice')
                    : this.env._t('Invoice');
            }
        }
        async _downloadInvoice(orderId) {
            try {
                console.log('Reimprimir factura posp')
                const [orderWithInvoice] = await this.rpc({
                    method: 'read',
                    model: 'pos.order',
                    args: [orderId, ['account_move']],
                    kwargs: { load: false },
                });
                if (orderWithInvoice && orderWithInvoice.account_move) {
                    await this.env.pos.do_action('pos_paraguay.factura_pos_boton_2', {
                        additional_context: {
                            active_ids: [orderWithInvoice.account_move],
                        },
                    });
                }
            } catch (error) {
                if (error instanceof Error) {
                    throw error;
                } else {
                    // NOTE: error here is most probably undefined
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Network Error'),
                        body: this.env._t('Unable to download invoice.'),
                    });
                }
            }
        }
        async _invoiceOrder() {
            const order = this.props.order;
            if (!order) return;

            const orderId = order.backendId;

            // Part 0.1. If already invoiced, print the invoice.
            if (this.isAlreadyInvoiced) {
                await this._downloadInvoice(orderId);
                return;
            }

            // Part 0.2. Check if order belongs to an active session.
            // If not, do not allow invoicing.
            if (order.isFromClosedSession) {
                this.showPopup('ErrorPopup', {
                    title: this.env._t('Session is closed'),
                    body: this.env._t('Cannot invoice order from closed session.'),
                });
                return;
            }

            // Part 1: Handle missing client.
            // Write to pos.order the selected client.
            if (!order.get_client()) {
                const { confirmed: confirmedPopup } = await this.showPopup('ConfirmPopup', {
                    title: this.env._t('Need customer to invoice'),
                    body: this.env._t('Do you want to open the customer list to select customer?'),
                });
                if (!confirmedPopup) return;

                const { confirmed: confirmedTempScreen, payload: newClient } = await this.showTempScreen(
                    'ClientListScreen'
                );
                if (!confirmedTempScreen) return;

                await this.rpc({
                    model: 'pos.order',
                    method: 'write',
                    args: [[orderId], { partner_id: newClient.id }],
                    kwargs: { context: this.env.session.user_context },
                });
            }

            // Part 2: Invoice the order.
            await this.rpc(
                {
                    model: 'pos.order',
                    method: 'action_pos_order_invoice',
                    args: [orderId],
                    kwargs: { context: this.env.session.user_context },
                },
                {
                    timeout: 30000,
                    shadow: true,
                }
            );

            // Part 3: Download invoice.
            await this._downloadInvoice(orderId);
            this.trigger('order-invoiced', orderId);
        }
        async _onClick() {
            try {
                await this._invoiceOrder();
            } catch (error) {
                if (isConnectionError(error)) {
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Network Error'),
                        body: this.env._t('Unable to invoice order.'),
                    });
                } else {
                    throw error;
                }
            }
        }
    };
    InvoiceButtonticket.template = 'InvoiceButton';
    Registries.Component.add(InvoiceButtonticket);

    return InvoiceButtonticket;
    // models.PosModel= models.PosModel.extend({
    //
    //     push_and_invoice_order: function(order){
    //     var self = this;
    //
    //
    //     var invoiced = new $.Deferred();
    //     var report = '';
    //
    //     if(!order.get_client()){
    //         invoiced.reject({code:400, message:'Missing Customer', data:{}});
    //         return invoiced;
    //     }
    //
    //     var order_id = this.db.add_order(order.export_as_JSON());
    //
    //     this.flush_mutex.exec(function(){
    //         var done = new $.Deferred(); // holds the mutex
    //
    //         // send the order to the server
    //         // we have a 30 seconds timeout on this push.
    //         // FIXME: if the server takes more than 30 seconds to accept the order,
    //         // the client will believe it wasn't successfully sent, and very bad
    //         // things will happen as a duplicate will be sent next time
    //         // so we must make sure the server detects and ignores duplicated orders
    //
    //         var transfer = self._flush_orders([self.db.get_order(order_id)], {timeout:30000, to_invoice:true});
    //
    //         transfer.fail(function(error){
    //             invoiced.reject(error);
    //             done.reject();
    //         });
    //
    //         // on success, get the order id generated by the server
    //         transfer.pipe(function(order_server_id){
    //             report = self.config.invoice_report_text
    //             // console.log(report)
    //             //self.chrome.do_action('point_of_sale.pos_invoice_report',{additional_context:{
    //             // self.chrome.do_action(report,{additional_context:{
    //             // generate the pdf and download it
    //             self.chrome.do_action(report,{additional_context:{
    //                 active_ids:order_server_id,
    //             }}).done(function () {
    //                 invoiced.resolve();
    //                 done.resolve();
    //             });
    //         });
    //
    //         return done;
    //
    //     });
    //
    //     return invoiced;
    // },
    //
    //
    //
    // });


});

