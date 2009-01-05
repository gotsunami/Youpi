/*
 * Class: ShoppingCart
 * Basic shopping cart implementation
 *
 * File:
 *
 *  shoppingcart.js
 *
 * Dependencies:
 *
 *  scritptaculous.js
 *
 * Constructor Parameters:
 *
 * container_id - string: name of parent DOM block container
 * varName - string: global variable name of instance, used internally for public interface definition
 *
 */
function ShoppingCart(container_id, varName)
{
	// Group: Constants
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Var: _instance_name
	 * Name of instance in global namespace
	 *
	 */
	var _instance_name = varName;
	/*
	 * Var: _container
	 * Parent DOM container
	 *
	 */ 
	var _container = document.getElementById(container_id);
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
			(itemsCount > 1 ? 's' : '') + ' to process' : 'Empty cart';
	}

	/*
	 * Function: _render
	 * Renders shopping cart
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
												className: 'nonempty',
												onclick: "location.href='/youpi/cart/'" }, [
								Builder.node('img', { src: '/media/themes/' + guistyle + '/img/misc/minicart.gif' }),
								_getArticlesCountMsg()
						  ]);

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
	 * Adds an item to the shopping cart
	 *
	 * Note:
	 * The *obj* object must have the following properties.
	 *
	 *  plugin_name - string: internal plugin name
	 *  userData - object: custom user data 
	 *
	 * Paremeters:
	 *  obj - object: arbitrary object
	 *  handler - function: custom function to execute after an item has been added
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

				var post = 	'plugin=' + obj.plugin_name + 
							'&userData=' + escape(Object.toJSON(obj.userData));
				// Check for cookie
				r.send('/youpi/cart/additem/', post);
			}
		);

		// Check for cookie
		xhr.send('/youpi/cart/cookiecheck/');
	}

	/*
	 * Function: deletePluginItem
	 * Deletes an item from the shopping cart
	 *
	 * Note:
	 * The *obj* object must have the following properties.
	 *
	 *  plugin_name - string: internal plugin name
	 *  idx - int: row index (in plugin context)
	 *
	 * Paremeters:
	 *  obj - object: arbitrary object
	 *  deleteAll - boolean: true to delete all plugin's items at once
	 *  handler - function: custom function to execute after an item has been deleted
	 *
	 */ 
	this.deletePluginItem = function(obj, deleteAll, handler) {
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
	 * Deletes an item from the shopping cart
	 *
	 * Note:
	 * The *obj* object must have the following properties.
	 *
	 *  plugin_name - string: internal plugin name
	 *  idx - int: row index (in plugin context)
	 *
	 * Paremeters:
	 *  obj - object: arbitrary object
	 *  handler - function: custom function to execute after an item has been deleted
	 *
	 */ 
	this.deleteAllPluginItems = function(plugin_name, handler) {
		this.deletePluginItem(plugin_name, true, handler);
	}

	// Main entry point
	_render();
}
