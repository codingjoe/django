(function($) {
    'use strict';
    var init = function($element, options) {
        var settings = $.extend({
            ajax: {
                data: function(params) {
                    return {
                        term: params.term,
                        page: params.page,
                        field_identifier: $element.data('field_identifier')
                    };
                }
            }
        }, options);

        $element.select2(settings);
    };

    $.fn.djangoAdminSelect2 = function(options) {
        var settings = $.extend({}, options);
        $.each(this, function(i, element) {
            var $element = $(element);
            init($element, settings);
        });
        return this;
    };

    $(function() {
        $('.admin-autocomplete').djangoAdminSelect2();
    });

    $(document).on('formset:added', (function() {
        return function(event, $newFormset) {
            var $widget;
            $widget = $newFormset.find('.admin-autocomplete');
            return init($widget);
        };
    })(this));

}(django.jQuery));
