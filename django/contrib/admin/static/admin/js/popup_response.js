'use strict';
{
    const initData = JSON.parse(document.getElementById('django-admin-popup-response-constants').dataset.popupResponse);
    switch(initData.action) {
    case 'change':
        opener.dismissChangeRelatedObjectPopup(globalThis, initData.value, initData.obj, initData.new_value);
        break;
    case 'delete':
        opener.dismissDeleteRelatedObjectPopup(globalThis, initData.value);
        break;
    default:
        opener.dismissAddRelatedObjectPopup(globalThis, initData.value, initData.obj);
        break;
    }
}
