from odoo import models, fields, api


class ComboModifierWizard(models.TransientModel):
    _name = 'combo.modifier.wizard'
    _description = 'Asistente para Modificar Combo'

    order_line_id = fields.Many2one(
        'sale.order.line',
        string='Línea de Pedido'
    )
    move_line_id = fields.Many2one(
        'account.move.line',
        string='Línea de Factura'
    )
    product_id = fields.Many2one(
        'product.product',
        string='Producto Combo',
        required=True
    )
    combo_line_ids = fields.One2many(
        'combo.modifier.wizard.line',
        'wizard_id',
        string='Componentes del Combo'
    )

    @api.model
    def default_get(self, fields_list):
        """Cargar datos por defecto del combo"""
        result = super().default_get(fields_list)
        
        order_line_id = self.env.context.get('default_order_line_id')
        move_line_id = self.env.context.get('default_move_line_id')
        product_id = self.env.context.get('default_product_id')

        if product_id:
            product = self.env['product.product'].browse(product_id)
            if product.product_tmpl_id.is_combo:
                combo_lines = []
                
                # Cargar desde línea de pedido existente si existe
                if order_line_id:
                    order_line = self.env['sale.order.line'].browse(order_line_id)
                    for combo_line in order_line.combo_component_lines:
                        combo_lines.append((0, 0, {
                            'product_id': combo_line.product_id.id,
                            'quantity': combo_line.quantity,
                            'original_quantity': combo_line.original_quantity,
                            'price_extra': combo_line.price_extra,
                            'required': combo_line.required,
                            'included': combo_line.included,
                        }))
                
                # Cargar desde línea de factura existente si existe
                elif move_line_id:
                    move_line = self.env['account.move.line'].browse(move_line_id)
                    for combo_line in move_line.combo_component_lines:
                        combo_lines.append((0, 0, {
                            'product_id': combo_line.product_id.id,
                            'quantity': combo_line.quantity,
                            'original_quantity': combo_line.original_quantity,
                            'price_extra': combo_line.price_extra,
                            'required': combo_line.required,
                            'included': combo_line.included,
                        }))
                
                # Si no hay líneas existentes, cargar desde la plantilla del producto
                else:
                    for combo_line in product.product_tmpl_id.combo_line_ids:
                        combo_lines.append((0, 0, {
                            'product_id': combo_line.product_id.id,
                            'quantity': combo_line.quantity,
                            'original_quantity': combo_line.quantity,
                            'price_extra': combo_line.price_extra,
                            'required': combo_line.required,
                            'included': True,
                        }))
                
                result['combo_line_ids'] = combo_lines

        return result

    def action_apply_changes(self):
        """Aplicar los cambios del combo"""
        if self.order_line_id:
            self._apply_to_sale_order()
        elif self.move_line_id:
            self._apply_to_account_move()
        
        return {'type': 'ir.actions.act_window_close'}

    def _apply_to_sale_order(self):
        """Aplicar cambios a la línea de pedido de venta"""
        # Eliminar líneas existentes
        self.order_line_id.combo_component_lines.unlink()
        
        # Crear nuevas líneas con las modificaciones
        for line in self.combo_line_ids:
            self.env['sale.order.combo.line'].create({
                'order_line_id': self.order_line_id.id,
                'product_id': line.product_id.id,
                'quantity': line.quantity,
                'original_quantity': line.original_quantity,
                'price_extra': line.price_extra,
                'required': line.required,
                'included': line.included,
            })

    def _apply_to_account_move(self):
        """Aplicar cambios a la línea de factura"""
        # Eliminar líneas existentes
        self.move_line_id.combo_component_lines.unlink()
        
        # Crear nuevas líneas con las modificaciones
        for line in self.combo_line_ids:
            self.env['account.move.combo.line'].create({
                'move_line_id': self.move_line_id.id,
                'product_id': line.product_id.id,
                'quantity': line.quantity,
                'original_quantity': line.original_quantity,
                'price_extra': line.price_extra,
                'required': line.required,
                'included': line.included,
            })


class ComboModifierWizardLine(models.TransientModel):
    _name = 'combo.modifier.wizard.line'
    _description = 'Línea del Asistente de Modificación de Combo'

    wizard_id = fields.Many2one(
        'combo.modifier.wizard',
        string='Asistente',
        required=True,
        ondelete='cascade'
    )
    product_id = fields.Many2one(
        'product.product',
        string='Componente',
        required=True
    )
    quantity = fields.Float(
        string='Cantidad',
        default=1.0,
        required=True
    )
    original_quantity = fields.Float(
        string='Cantidad Original',
        help="Cantidad original del componente en el combo"
    )
    price_extra = fields.Float(
        string='Precio Extra',
        default=0.0
    )
    required = fields.Boolean(
        string='Requerido',
        default=True
    )
    included = fields.Boolean(
        string='Incluido',
        default=True,
        help="Si está desmarcado, este componente será eliminado del combo"
    )

    @api.constrains('quantity')
    def _check_quantity(self):
        """Validar que la cantidad sea positiva si está incluida"""
        for record in self:
            if record.included and record.quantity <= 0:
                raise models.ValidationError("La cantidad debe ser mayor que cero para componentes incluidos")

    @api.onchange('included')
    def _onchange_included(self):
        """Cuando se desmarca incluido, resetear cantidad a 0"""
        if not self.included:
            self.quantity = 0.0
        elif self.quantity == 0.0:
            self.quantity = self.original_quantity or 1.0

