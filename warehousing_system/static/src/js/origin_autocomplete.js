/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, useRef, onMounted } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class OriginAutocompleteWidget extends Component {
    setup() {
        this.orm = useService("orm");
        this.state = useState({
            suggestions: [],
            showDropdown: false,
            selectedIndex: -1,
            inputValue: this.props.record.data[this.props.name] || ""
        });
        this.inputRef = useRef("originInput");
        
        onMounted(() => {
            this.setupInputEvents();
        });
    }

    setupInputEvents() {
        const input = this.inputRef.el;
        if (input) {
            input.addEventListener('input', this.onInput.bind(this));
            input.addEventListener('keydown', this.onKeyDown.bind(this));
            input.addEventListener('blur', this.onBlur.bind(this));
            input.addEventListener('focus', this.onFocus.bind(this));
        }
    }

    async onInput(event) {
        const query = event.target.value;
        this.state.inputValue = query;
        
        // Update the record field
        this.props.record.update({ [this.props.name]: query });
        
        if (query && query.length >= 2) {
            try {
                const suggestions = await this.orm.call(
                    'stock.picking',
                    'search_memo_codes',
                    [query]
                );
                this.state.suggestions = suggestions || [];
                this.state.showDropdown = this.state.suggestions.length > 0;
                this.state.selectedIndex = -1;
            } catch (error) {
                console.error('Error fetching suggestions:', error);
                this.state.suggestions = [];
                this.state.showDropdown = false;
            }
        } else {
            this.state.suggestions = [];
            this.state.showDropdown = false;
        }
    }

    onKeyDown(event) {
        if (!this.state.showDropdown) return;

        switch (event.key) {
            case 'ArrowDown':
                event.preventDefault();
                this.state.selectedIndex = Math.min(
                    this.state.selectedIndex + 1,
                    this.state.suggestions.length - 1
                );
                break;
            case 'ArrowUp':
                event.preventDefault();
                this.state.selectedIndex = Math.max(this.state.selectedIndex - 1, -1);
                break;
            case 'Enter':
                event.preventDefault();
                if (this.state.selectedIndex >= 0) {
                    this.selectSuggestion(this.state.suggestions[this.state.selectedIndex]);
                }
                break;
            case 'Escape':
                this.state.showDropdown = false;
                this.state.selectedIndex = -1;
                break;
        }
    }

    onBlur() {
        // Delay hiding dropdown to allow for click events
        setTimeout(() => {
            this.state.showDropdown = false;
            this.state.selectedIndex = -1;
        }, 200);
    }

    onFocus() {
        if (this.state.suggestions.length > 0) {
            this.state.showDropdown = true;
        }
    }

    async selectSuggestion(suggestion) {
        this.state.inputValue = suggestion.code;
        this.state.showDropdown = false;
        this.state.selectedIndex = -1;
        this.state.suggestions = [];
        
        try {
            // Update origin field
            await this.props.record.update({
                [this.props.name]: suggestion.code
            });
            
            // Update financial_id field separately using the ORM service
            if (this.props.record.fields.financial_id) {
                await this.orm.call(
                    this.props.record.resModel,
                    'write',
                    [
                        [this.props.record.resId],
                        { 'financial_id': suggestion.id }
                    ]
                );
                
                // Reload the record to reflect changes
                await this.props.record.load();
            }
        } catch (error) {
            console.error('Error updating fields:', error);
            // Fallback: just update the origin field
            await this.props.record.update({
                [this.props.name]: suggestion.code
            });
        }
        
        // Update input value
        if (this.inputRef.el) {
            this.inputRef.el.value = suggestion.code;
        }
    }

    onSuggestionClick(suggestion) {
        this.selectSuggestion(suggestion);
    }

    get dropdownStyle() {
        return this.state.showDropdown ? 'display: block;' : 'display: none;';
    }

    getSuggestionClass(index) {
        return index === this.state.selectedIndex ? 
            'dropdown-item active' : 'dropdown-item';
    }
}

OriginAutocompleteWidget.template = "warehousing_system.OriginAutocompleteWidget";
OriginAutocompleteWidget.props = {
    ...standardFieldProps,
    placeholder: { type: String, optional: true },
};

export const originAutocompleteWidget = {
    component: OriginAutocompleteWidget,
    displayName: "Origin Autocomplete",
    supportedTypes: ["char"],
};

registry.category("fields").add("origin_autocomplete_widget", originAutocompleteWidget);