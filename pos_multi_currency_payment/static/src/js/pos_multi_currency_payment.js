odoo.define('pos_multi_currency_payment', function (require) {
    var models = require('point_of_sale.models');
    var screens = require('point_of_sale.screens');
    var utils = require('web.utils');
    var round_pr = utils.round_precision;
    var round_di = utils.round_decimals;
    var core = require('web.core');
    var _t = core._t;
    var rpc = require('web.rpc');


    models.load_models([
        {
            model: 'res.currency',
            fields: [],

            loaded: function (self, currencies) {
                self.currencies = currencies;
                self.currency_by_id = {};
                for (var i = 0; i < currencies.length; i++) {
                    self.currency_by_id[currencies[i]['id']] = currencies[i];
                }
            }
        }
    ]);

    screens.PaymentScreenWidget.include({
        renderElement: function () {
            var self = this;
            this._super();
            var a = 0;
            var order = this.pos.get_order();

            // if (order.invoice_to_pay ){
            //         order.selected_currency=order.pos.currency_by_id[order.invoice_to_pay.currency_id[0]];
            //     }
            // else{
            order.selected_currency = this.pos.currency_by_id[this.pos.currency.id];
            // }




            this.$('.select-currency').on('change', function (e) {


                //Funciona
                var currency_id = parseInt(self.$('.select-currency').val());


                var selected_currency = self.pos.currency_by_id[currency_id];
                // console.log(selected)
                // var company_currency = self.pos.currency_by_id[self.pos.currency['id']];
                var company_currency = self.pos.currency_by_id[self.pos.company.currency_id[0]];
                var pos_currency = self.pos.currency_by_id[self.pos.currency['id']];
                // console.log('order');

                // console.log('this.pos');
                // console.log(self.pos);
                // console.log('this');
                // console.log(self);
                /*
                    Return action if have not selected currency or company currency is 0
                 */
                if (!selected_currency || company_currency['rate'] == 0) {

                    return;
                }
                order.selected_currency = selected_currency;
                // console.log('bbb');
                //
                if (selected_currency == pos_currency){
                    var currency_covert_text = self.format_currency_no_symbol(1 );
                }
                else if (selected_currency['rate_venta'] ==1){
                     var currency_covert_text ='< 0,05' ;
                }
                else {
                    var currency_covert_text = self.format_currency_no_symbol(selected_currency['rate_venta'] / pos_currency['rate_venta']);

                }

                // console.log('ccc');
                // add current currency rate to payment screen
                var $currency_covert = self.el.querySelector('.currency-covert');
                if ($currency_covert) {
                    $currency_covert.textContent = '1 ' + selected_currency['name'] + ' = ' + currency_covert_text + ' ' + pos_currency['name'];
                }
                // console.log('ddd');
                var selected_paymentline = order.selected_paymentline;
                if (selected_paymentline) {
                    selected_paymentline.set_amount("0");
                    self.inputbuffer = "";
                } else {
                    order.add_paymentline(self.pos.cashregisters[0]);
                }
                // console.log(order);
                // console.log('eee');
                if (order.invoice_to_pay){
                    var due=order.invoice_to_pay.residual;
                    }
                else{
                    var due = order.get_due();
                }

                // var amount_full_paid = due / selected_currency['rate'] / company_currency['rate'];
                if (selected_currency == pos_currency){
                    var amount_full_paid = due;

                }
                else if (selected_currency['rate_venta'] ==1){
                     var amount_full_paid = due * (1/  pos_currency['rate_venta']);
                }
                else {
                     var amount_full_paid = due * (selected_currency['rate_venta'] / pos_currency['rate_venta']);
                    // var currency_covert_text = self.format_currency_no_symbol(selected_currency['rate'] / pos_currency['rate']);

                }
                // var amount_full_paid = due / (1 / selected_currency['rate']) ;
                var due_currency = self.format_currency_no_symbol(amount_full_paid);
                var $currency_paid_full = self.el.querySelector('.currency-paid-full');
                if ($currency_paid_full) {
                    $currency_paid_full.textContent = due_currency;
                }
                // console.log('fff');
                self.add_currency_to_payment_line();
                // console.log('ggg');
                self.render_paymentlines();
                // console.log('hhh');
            });
            this.$('.update-rate').on('click', function (e) {
                var currency_id = parseInt($('.select-currency').val());
                var selected_currency = self.pos.currency_by_id[currency_id];
                self.selected_currency = selected_currency;
                if (selected_currency) {
                    self.hide();
                    self.gui.show_popup('textarea', {
                        title: _t('Input Rate'),
                        value: self.selected_currency['rate'],
                        confirm: function (rate) {
                            var selected_currency = self.selected_currency;
                            selected_currency['rate'] = parseFloat(rate);
                            self.show();
                            self.renderElement();
                            var params = {
                                name: new Date(),
                                currency_id: self.selected_currency['id'],
                                rate: parseFloat(rate),
                            }
                            return rpc.query({
                                model: 'res.currency.rate',
                                method: 'create',
                                args:
                                    [params],
                                context: {}
                            }).then(function (rate_id) {
                                return rate_id;
                            }).then(function () {
                                self.gui.close_popup();
                            }).fail(function (type, error) {
                                if (error.code === 200) {
                                    event.preventDefault();
                                    self.gui.show_popup('error', {
                                        'title': _t('!!! ERROR !!!'),
                                        'body': error.data.message,
                                    });
                                }
                            });
                        },
                        cancel: function () {
                            self.show();
                            self.renderElement();
                        }
                    });
                }

            })
        },
        add_currency_to_payment_line: function (line) {
            var order = this.pos.get_order();
            // console.log('zzz');
            line = order.selected_paymentline;
            // console.log('yyy');
            line.selected_currency = order.selected_currency;
            // console.log('xxx');
        }
    })
    ;

    var _super_paymentlinne = models.Paymentline.prototype;
    models.Paymentline = models.Paymentline.extend({
        initialize: function (attributes, options) {
            _super_paymentlinne.initialize.apply(this, arguments);
            this.amount_currency = this.amount_currency || 0;
            this.currency_id = this.currency_id || null;

        },
        set_amount: function (value) {
            _super_paymentlinne.set_amount.apply(this, arguments);
            var order = this.pos.get_order();
            var company_currency = this.pos.currency_by_id[this.pos.company.currency_id[0]];
            var pos_currency = this.pos.currency_by_id[this.pos.currency['id']];

            var amount = parseFloat(value);
            if (this.selected_currency) {
                this.currency_id = this.selected_currency['id'];
                this.amount_currency = amount;


                // this.amount = this.amount_currency * this.selected_currency['rate'] / company_currency['rate'] ;
                if (this.selected_currency == pos_currency)
                {
                    this.amount= this.amount_currency;
                }
                else if (this.selected_currency['rate_venta'] ==1){
                      this.amount = this.amount_currency / (1/  pos_currency['rate_venta']);
                }
                else {
                    this.amount = this.amount_currency / (this.selected_currency['rate_venta'] / pos_currency['rate_venta']);
                    // this.amount = this.amount_currency * (1/ this.selected_currency['rate']) ;
                    // this.amount = this.amount_currency * this.selected_currency['rate'] / pos_currency['rate'];
                }

            } else if (order.selected_currency) {
                this.selected_currency = order.selected_currency;
                this.amount_currency = amount;

                // this.amount = this.amount_currency * this.selected_currency['rate'] / company_currency['rate'] ;
                // this.amount = this.amount_currency * (1 / this.selected_currency['rate'] ) ;
                if (this.selected_currency == pos_currency)
                {
                    this.amount= this.amount_currency;
                }
                else if ( this.selected_currency['rate_venta'] ==
                    1){
                      this.amount = this.amount_currency / (1/  pos_currency['rate_venta']);
                }
                else {
                    this.amount = this.amount_currency / ( this.selected_currency['rate_venta'] / pos_currency['rate_venta']);
                }
                this.currency_id = this.selected_currency['id'];


                // if (this.currency_id != pos_currency)
                // {
                //     // this.amount = this.amount_currency * (1/ this.selected_currency['rate']) ;
                //      this.amount = this.amount_currency * this.selected_currency['rate'] / pos_currency['rate'] ;
                // }
                // else
                //     {
                //         this.amount = this.amount_currency  ;
                //     }

            }
            this.trigger('change', this);
        },

        export_as_JSON: function () {
            var json = _super_paymentlinne.export_as_JSON.apply(this, arguments);
            if (this.currency_id) {
                json['currency_id'] = this.currency_id;
            }
            if (this.amount_currency) {
                json['amount_currency'] = this.amount_currency;
            }

            return json;
        },
        export_for_printing: function () {
            var json = _super_paymentlinne.export_for_printing.apply(this, arguments);
            if (this.currency_id) {
                json['currency_id'] = this.currency_id;
            }
            if (this.selected_currency) {
                json['selected_currency'] = this.selected_currency;
            }
            if (this.amount_currency) {
                json['amount_currency'] = this.amount_currency;
            }
            return json;
        },
        init_from_JSON: function (json) {
            var res = _super_paymentlinne.init_from_JSON.apply(this, arguments);
            if (json['currency_id']) {
                var company_currency = this.pos.currency_by_id[this.pos.currency['id']];
                this['selected_currency'] = this.pos.currency_by_id[json['currency_id']];
                this['amount_currency'] = round_di(this.amount * company_currency['rate_venta'] / this['selected_currency']['rate_venta'] || 0, this.pos.currency.decimals);
                this['currency_id'] = this.pos.currency_by_id[json['currency_id']]['id'];
            }

            return res;
        }
    });
})
;
