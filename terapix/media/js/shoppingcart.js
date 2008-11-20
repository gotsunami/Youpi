
/*
 * Class: ShoppingCart
 * Basic shopping cart implementation
 *
 * Note:
 *
 * Please note that this page documents Javascript code. <ShoppingCart> is a pseudo-class, 
 * it provides encapsulation and basic public/private features.
 *
 * Constructor Parameters:
 *
 * container_id - string: name of parent DOM block container
 * varName - string: global variable name of instance, used internally for public interface definition
 *
 */
function ShoppingCart(container_id, varName)
{
	// Name of instance if global namespace
	var instance_name = varName;
	var container = document.getElementById(container_id);

	var itemsCount = 0;
	var itemCaption = ['item', 'items'];

	function getArticlesCountMsg() {
		return itemsCount ? itemsCount + ' ' + 
			(itemsCount > 1 ? itemCaption[1] : itemCaption[0]) + ' to process' : 'Empty cart';
	}

	function render() {
		var xhr = new HttpRequest(
			null,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				itemsCount = resp['count'];
				var div = document.createElement('div');
				div.setAttribute('id', 'shoppingCart');
				div.setAttribute('class', 'nonempty');
				div.setAttribute('onclick', 'location.href="/youpi/cart/";');

				var img = document.createElement('img');
				img.setAttribute('src', '/media/themes/' + guistyle + '/img/misc/minicart.gif');
				div.appendChild(img);
				div.appendChild(document.createTextNode(getArticlesCountMsg()));
				removeAllChildrenNodes(container);
				container.appendChild(div);
			}
		);

		// Count items
		xhr.send('/youpi/cart/itemsCount/');
	}

	// Refresh display
	this.refresh = function() {
		render();
	}

	function showToolTip() {}

	function removeAllChildrenNodes(node)
	{
		// Element ?
		if (node.nodeType != 1)
			return;
	
		if (node.hasChildNodes()) {
			for (var n=0; n < node.childNodes.length; n++) {
				node.removeChild(node.childNodes[n]);
			}
		}
	}

	/*
	 * Adds an item to the cart
	 *
	 */
	// handler: called when processing added
	function addItem(json, handler) {
		var xhr = new HttpRequest(
			container.id,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				var nb = resp['data'].length;
				render();
				// Call custom handler
				if (handler) handler();
			}
		);

		var post = 'plugin=' + json['plugin_name'] + '&userData=' + escape(json['userData']);
		// Check for cookie
		xhr.send('/youpi/cart/additem/', post);
	}

	// json: { 'plugin_name' : 'name', 'userData' : data }
	// handler: called when processing added
	this.addProcessing = function(json, handler) {
		var xhr = new HttpRequest(
			container.id,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				addItem(json, handler);
			}
		);

		// Check for cookie
		xhr.send('/youpi/cart/cookiecheck/');
	}

	/*
	 * Deletes an item in the cart (for a plugin)
	 *
	 */
	// json: { 'plugin_name' : 'name', 'idx' : index of row in plugin context }
	this.deletePluginItem = function(json, handlerAfterDelete) {
		// Custom handler called upon successful deletion
		var chandler = handlerAfterDelete ? handlerAfterDelete : null;
		var xhr = new HttpRequest(
			container.id,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				var nb = resp['data'].length;
				render();
				if (chandler) chandler();
			}
		);

		var post = 'plugin=' + json['plugin_name'] + '&idx=' + json['idx'];
		// Check for cookie
		xhr.send('/youpi/cart/delitem/', post);
	}

	/*
	 * Deletes all items of one plugin in the cart
	 *
	 */
	this.deleteAllPluginItems = function(plugin_name, handlerAfterDelete) {
		// Custom handler called upon successful deletion
		var chandler = handlerAfterDelete ? handlerAfterDelete : null;
		var xhr = new HttpRequest(
			container.id,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				var nb = resp['data'].length;
				render();
				if (chandler) chandler();
			}
		);

		var post = 'plugin=' + plugin_name;
		// Check for cookie
		xhr.send('/youpi/cart/delitem/', post);
	}

	// Main entry point
	render();
}
