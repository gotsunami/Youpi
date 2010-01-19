/*****************************************************************************
 *
 * Copyright (c) 2008-2009 Terapix Youpi development team. All Rights Reserved.
 *                    Mathias Monnerville <monnerville@iap.fr>
 *                    Gregory Semah <semah@iap.fr>
 *
 * This program is Free Software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 *****************************************************************************/

/*
 * Class: ProcessingCart
 * Basic processing cart implementation
 *
 * File:
 *
 *  processingcart.js
 *
 * Dependencies:
 *
 *  scritptaculous.js
 *
 * Constructor Parameters:
 *
 * container - string or DOM: name of parent DOM block container
 *
 */
function ProcessingCart(container)
{
	// Group: Constants
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Var: _container
	 * Parent DOM container
	 *
	 */ 
	var _container = $(container);
	/*
	 * Var: _itemsCount
	 * Number of items in cart
	 *
	 */ 
	var itemsCount = 0;


	// Group: Functions
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Function: _getArticlesCountMsg
	 * Cart text rendering
	 *
	 */ 
	function _getArticlesCountMsg() {
		return itemsCount ? itemsCount + ' item' + 
			(itemsCount > 1 ? 's' : '') : 'Empty cart';
	}

	/*
	 * Function: _render
	 * Renders processing cart
	 *
	 */ 
	function _render() {
		var xhr = new HttpRequest(
			null,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				itemsCount = resp.count;
				var div = Builder.node('div', { id: 'shoppingCart',
												className: 'nonempty' }, [
								Builder.node('img', { src: '/media/themes/' + guistyle + '/img/misc/minicart.png' }),
								_getArticlesCountMsg()
						  ]);
				div.observe('click', function(event) { location.href = '/youpi/cart/'; });

				// Clear contents
				_container.update();
				_container.appendChild(div);
			}
		);

		// Count items
		xhr.send('/youpi/cart/itemsCount/');
	}

	/*
	 * Function: refresh
	 * Updates cart rendering
	 *
	 */ 
	this.refresh = function() {
		_render();
	}

	/*
	 * Function: addProcessing
	 * Adds an item to the processing cart
	 *
	 * Parameters:
	 *  obj - object: arbitrary object
	 *  handler - function: custom function to execute after an item has been added
	 *
	 * Note:
	 * The *obj* object must have the following properties.
	 *
	 *  plugin_name - string: internal plugin name
	 *  userData - object: custom user data 
	 *
	 */ 
	this.addProcessing = function(obj, handler) {
		var xhr = new HttpRequest(
			null,
			null,
			// Custom handler for results
			function(resp) {
				var r = new HttpRequest(
					null,
					null,
					function(resp) {
						var nb = resp['data'].length;
						_render();
						// Call custom handler
						if (handler) handler();
					}
				);

				var post = {
					plugin: obj.plugin_name,
					userData: Object.toJSON(obj.userData)
				};					
				// Check for cookie
				r.send('/youpi/cart/additem/', $H(post).toQueryString());
			}
		);

		// Check for cookie
		xhr.send('/youpi/cart/cookiecheck/');
	}

	/*
	 * Function: deletePluginItem
	 * Deletes an item from the processing cart
	 *
	 * Parameters:
	 *  obj - object: arbitrary object
	 *  handler - function: custom function to execute after an item has been deleted
	 *  deleteAll - boolean: true to delete all plugin's items at once
	 *
	 * Note:
	 * The *obj* object must have the following properties.
	 *
	 * plugin_name - string: internal plugin name
	 * idx - int: row index (in plugin context)
	 *
	 */ 
	this.deletePluginItem = function(obj, handler, deleteAll) {
		var handler = typeof handler == 'function' ? handler : null;
		var deleteAll = typeof deleteAll == 'boolean' ? deleteAll : false;

		var xhr = new HttpRequest(
			null,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				var nb = resp.data.length;
				_render();
				if (handler) handler();
			}
		);

		var post = 'plugin=' + obj.plugin_name;
		if (!deleteAll)
			post += '&idx=' + obj.idx;
		xhr.send('/youpi/cart/delitem/', post);
	}

	/*
	 * Function: deleteAllPluginItem
	 * Deletes an item from the processing cart
	 *
	 * Parameters:
	 *  obj - object: arbitrary object
	 *  handler - function: custom function to execute after an item has been deleted
	 *
	 * Note:
	 * The *obj* object must have the following properties.
	 *
	 *  plugin_name - string: internal plugin name
	 *  idx - int: row index (in plugin context)
	 *
	 */ 
	this.deleteAllPluginItems = function(plugin_name, handler) {
		this.deletePluginItem(plugin_name, true, handler);
	}

	// Main entry point
	_render();
}
