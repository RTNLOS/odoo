/** @odoo-module **/
import { Many2XAutocomplete } from "@web/views/fields/relational_utils";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

patch(Many2XAutocomplete.prototype, {
    async onSearchMore(request) {
        const { resModel, getDomain, context, fieldString } = this.props;
        
        let domain = getDomain();
        let dynamicFilters = [];
        let searchContext = { ...context };
        
        if (resModel === 'product.product' && 
            context.filter_picking_code === 'outgoing' && 
            context.filter_customer_id && 
            (context.filter_location_id || context.filter_warehouse_id)) {
            
            const availableProducts = await this.orm.call(resModel, "name_search", [], {
                name: "",
                args: domain,
                operator: "ilike",
                limit: 1000,
                context: searchContext,
            });
            
            if (availableProducts.length > 0) {
                const productIds = availableProducts.map(p => p[0]);
                domain = [...domain, ['id', 'in', productIds]];
            } else {
                domain = [...domain, ['id', 'in', []]];
            }
        }
        
        if (request.length) {
            const nameGets = await this.orm.call(resModel, "name_search", [], {
                name: request,
                args: domain,
                operator: "ilike", 
                limit: this.props.searchMoreLimit,
                context: searchContext,
            });

            dynamicFilters = [
                {
                    description: _t("Quick search: %s", request),
                    domain: [["id", "in", nameGets.map((nameGet) => nameGet[0])]],
                },
            ];
        }

        const title = _t("Search: %s", fieldString);
        this.selectCreate({
            domain,
            context: searchContext,
            filters: dynamicFilters,
            title,
        });
    }
});