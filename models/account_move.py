from odoo import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    is_combo_line = fields.Boolean(
        string='Es Línea de Combo',
        default=False,
        help="Indica si esta línea es parte de un combo"
    )
    combo_parent_line_id = fields.Many2one(
        'account.move.line',
        string='Línea Padre del Combo',
        help="Referencia a la línea principal del combo"
    )
    combo_child_line_ids = fields.One2many(
        'account.move.line',
        'combo_parent_line_id',
        string='Líneas Hijas del Combo',
        help="Componentes del combo"
    )
    combo_component_lines = fields.One2many(
        'account.move.combo.line',
        'move_line_id',
        string='Componentes del Combo Modificados',
        help="Componentes del combo con cantidades personalizadas"
    )

    @api.model
    def create(self, vals):
        """Override create to handle combo line creation"""
        result = super().create(vals)
        
        # Si es un producto combo, crear las líneas de componentes
        if result.product_id and result.product_id.product_tmpl_id.is_combo:
            result._create_combo_lines()
        
        return result

    def _create_combo_lines(self):
        """Crear líneas de componentes para un combo"""
        if not self.product_id.product_tmpl_id.is_combo:
            return

        # Eliminar líneas existentes si las hay
        self.combo_component_lines.unlink()

        # Crear líneas para cada componente del combo
        for combo_line in self.product_id.product_tmpl_id.combo_line_ids:
            self.env['account.move.combo.line'].create({
                'move_line_id': self.id,
                'product_id': combo_line.product_id.id,
                'quantity': combo_line.quantity * self.quantity,
                'original_quantity': combo_line.quantity,
                'price_extra': combo_line.price_extra,
                'required': combo_line.required,
                'included': True,
            })

    def write(self, vals):
        """Override write to handle combo line updates"""
        result = super().write(vals)
        
        # Si cambia la cantidad del combo, actualizar componentes
        if 'quantity' in vals:
            for line in self:
                if line.product_id and line.product_id.product_tmpl_id.is_combo:
                    line._update_combo_quantities()
        
        return result

    def _update_combo_quantities(self):
        """Actualizar cantidades de componentes cuando cambia la cantidad del combo"""
        for combo_line in self.combo_component_lines:
            if combo_line.included:
                combo_line.quantity = combo_line.original_quantity * self.quantity

    def action_open_combo_modifier(self):
        """Abrir el wizard para modificar el combo"""
        if not self.product_id.product_tmpl_id.is_combo:
            return

        return {
            'type': 'ir.actions.act_window',
            'name': 'Modificar Combo',
            'res_model': 'combo.modifier.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_move_line_id': self.id,
                'default_product_id': self.product_id.id,
            }
        }


class AccountMoveComboLine(models.Model):
    _name = 'account.move.combo.line'
    _description = 'Línea de Componente de Combo en Factura'
    _order = 'sequence, id'

    move_line_id = fields.Many2one(
        'account.move.line',
        string='Línea de Factura',
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
        help="Si está desmarcado, este componente fue eliminado del combo"
    )
    sequence = fields.Integer(
        string='Secuencia',
        default=10
    )

    @api.constrains('quantity')
    def _check_quantity(self):
        """Validar que la cantidad sea positiva si está incluida"""
        for record in self:
            if record.included and record.quantity <= 0:
                raise models.ValidationError("La cantidad debe ser mayor que cero para componentes incluidos")

