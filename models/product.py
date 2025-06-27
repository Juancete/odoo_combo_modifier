from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_combo = fields.Boolean(
        string='Es Combo',
        default=False,
        help="Marcar si este producto es un combo que contiene otros productos"
    )
    combo_line_ids = fields.One2many(
        'product.combo.line',
        'product_tmpl_id',
        string='Componentes del Combo',
        help="Lista de productos que componen este combo"
    )

    @api.model
    def create(self, vals):
        """Override create to handle combo creation"""
        result = super().create(vals)
        if result.is_combo and not result.combo_line_ids:
            # Si es un combo pero no tiene componentes, podemos crear algunos por defecto
            # o simplemente dejar que el usuario los configure manualmente
            pass
        return result

    def write(self, vals):
        """Override write to handle combo updates"""
        result = super().write(vals)
        if 'is_combo' in vals and not vals['is_combo']:
            # Si se desmarca como combo, eliminar los componentes
            self.combo_line_ids.unlink()
        return result


class ProductComboLine(models.Model):
    _name = 'product.combo.line'
    _description = 'Línea de Componente de Combo'
    _order = 'sequence, id'

    product_tmpl_id = fields.Many2one(
        'product.template',
        string='Producto Combo',
        required=True,
        ondelete='cascade'
    )
    product_id = fields.Many2one(
        'product.product',
        string='Componente',
        required=True,
        domain="[('sale_ok', '=', True)]"
    )
    quantity = fields.Float(
        string='Cantidad',
        default=1.0,
        required=True,
        help="Cantidad por defecto de este componente en el combo"
    )
    sequence = fields.Integer(
        string='Secuencia',
        default=10,
        help="Orden de los componentes en el combo"
    )
    required = fields.Boolean(
        string='Requerido',
        default=True,
        help="Si está marcado, este componente no puede ser eliminado del combo"
    )
    price_extra = fields.Float(
        string='Precio Extra',
        default=0.0,
        help="Precio adicional por este componente (puede ser negativo para descuentos)"
    )

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Actualizar información cuando se cambia el producto"""
        if self.product_id:
            # Podemos establecer valores por defecto basados en el producto
            pass

    @api.constrains('quantity')
    def _check_quantity(self):
        """Validar que la cantidad sea positiva"""
        for record in self:
            if record.quantity <= 0:
                raise models.ValidationError("La cantidad debe ser mayor que cero")

