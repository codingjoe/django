'use strict';
{
    // Call function fn when the DOM is loaded and ready. If it is already
    // loaded, call the function now.
    // http://youmightnotneedjquery.com/#ready
    function ready(fn) {
        if (document.readyState !== 'loading') {
            fn();
        } else {
            document.addEventListener('DOMContentLoaded', fn);
        }
    }

    ready(() => {
        function handleClick(event) {
            event.preventDefault();
            const params = new URLSearchParams(globalThis.location.search);
            if (params.has('_popup')) {
                globalThis.close(); // Close the popup.
            } else {
                globalThis.history.back(); // Otherwise, go back.
            }
        }

        for (const el of document.querySelectorAll('.cancel-link')) {
            el.addEventListener('click', handleClick);
        }
    });
}
