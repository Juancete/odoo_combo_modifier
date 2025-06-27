/** @odoo-module **/

import { registry } from "@web/core/registry";
import { ListController } from "@web/views/list/list_controller";
import { useService } from "@web/core/utils/hooks";

export class ComboModifierController extends ListController {
    setup() {
        super.setup();
        this.action = useService("action");
        this.dialog = useService("dialog");
    }

    /**
     * Abrir el wizard de modificación de combo
     */
    async openComboModifier(record) {
        const productId = record.data.product_id && record.data.product_id[0];
        const isCombo = record.data.product_id && record.data.product_id.length > 1 && 
                       record.data.product_id[1].includes('combo');

        if (!productId || !isCombo) {
            return;
        }

        const context = {
            default_product_id: productId,
        };

        // Determinar si es línea de pedido o factura
        if (record.resModel === 'sale.order.line') {
            context.default_order_line_id = record.resId;
        } else if (record.resModel === 'account.move.line') {
            context.default_move_line_id = record.resId;
        }

        return this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Modificar Combo',
            res_model: 'combo.modifier.wizard',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: context,
        });
    }

    /**
     * Manejar click en botón de modificar combo
     */
    async onComboModifierClick(ev) {
        ev.preventDefault();
        ev.stopPropagation();
        
        const record = this.model.root.records.find(r => 
            r.resId === parseInt(ev.target.closest('tr').dataset.id)
        );
        
        if (record) {
            await this.openComboModifier(record);
        }
    }
}

// Registrar el controlador personalizado
registry.category("views").add("combo_modifier_list", {
    ...registry.category("views").get("list"),
    Controller: ComboModifierController,
});

// Funciones auxiliares para mejorar la experiencia del usuario
export const ComboModifierUtils = {
    /**
     * Validar que las cantidades sean válidas
     */
    validateQuantities(comboLines) {
        const errors = [];
        
        comboLines.forEach((line, index) => {
            if (line.included && line.quantity <= 0) {
                errors.push(`La cantidad del componente ${line.product_name} debe ser mayor que cero`);
            }
        });
        
        return errors;
    },

    /**
     * Calcular el precio total del combo modificado
     */
    calculateComboPrice(comboLines, basePrice = 0) {
        let totalExtra = 0;
        
        comboLines.forEach(line => {
            if (line.included) {
                totalExtra += line.price_extra * line.quantity;
            }
        });
        
        return basePrice + totalExtra;
    },

    /**
     * Formatear la descripción del combo para mostrar en la línea
     */
    formatComboDescription(comboLines) {
        const includedComponents = comboLines.filter(line => line.included);
        
        if (includedComponents.length === 0) {
            return "Combo vacío";
        }
        
        const descriptions = includedComponents.map(line => 
            `${line.product_name} (${line.quantity})`
        );
        
        return descriptions.join(', ');
    }
};

// Mejorar la interfaz con eventos personalizados
document.addEventListener('DOMContentLoaded', function() {
    // Agregar estilos CSS personalizados para los botones de combo
    const style = document.createElement('style');
    style.textContent = `
        .combo-modifier-btn {
            background-color: #007bff;
            color: white;
            border: none;
            padding: 4px 8px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            margin-left: 5px;
        }
        
        .combo-modifier-btn:hover {
            background-color: #0056b3;
        }
        
        .combo-modifier-btn:disabled {
            background-color: #6c757d;
            cursor: not-allowed;
        }
        
        .combo-component-excluded {
            opacity: 0.5;
            text-decoration: line-through;
        }
        
        .combo-component-modified {
            background-color: #fff3cd;
            border-left: 3px solid #ffc107;
            padding-left: 5px;
        }
    `;
    document.head.appendChild(style);
});

