/*
 * Class: TagWidget
 * Widget implementing tags
 *
 * For convenience, private data member names (both variables and functions) start with an underscore.
 *
 * Constructor Parameters:
 *
 * container - string or DOM object: name of parent DOM block container
 *
 */
function TagWidget(container, name) {
	// Group: Constants
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Var: _container
	 * DOM container
	 *
	 */
	var _container = null;
	/*
	 * Var: _root
	 * Base DOM container
	 *
	 */
	var _root;


	// Group: Variables
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Var: _attrs
	 * Tag's attributes
	 *
	 */
	var _attrs;


	// Group: Functions
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Function: update
	 * Updates widget rendering
	 *
	 */ 
	this.update = function() {
		_update();
	}

	/*
	 * Function: _update
	 * Updates widget rendering
	 *
	 */ 
	function _update() {
		if (!_attrs.get('name')) return;

		_root.writeAttribute('style', _attrs.get('style'));
		_root.update(_attrs.get('name'));
	}

	/*
	 * Function: setName
	 * Sets tag name
	 *
	 */ 
	this.setName = function(name) {
		if (typeof name != 'string') {
			throw "setName expects a string!";
			return;
		}
		_attrs.set('name', name);
	}

	/*
	 * Function: reset
	 * Reset all attributes to default values
	 *
	 */ 
	this.reset = function() {
		_reset();
	}

	/*
	 * Function: _reset
	 * Reset all attributes to default values
	 *
	 */ 
	function _reset () {
		// Default attributes
		_attrs = $H({
			name: null, 
			cdate: null, 
			owner: null, 
			style: 'background-color: brown; color: white', 
			comment: null
		});

		_update();
	}

	/*
	 * Function: setStyle
	 * Sets tag CSS style
	 *
	 * Parameters:
	 *  style - string: raw CSS style
	 *
	 */ 
	this.setStyle = function(style) {
		if (typeof style != 'string') {
			throw "setStyle expects a string!";
			return;
		}

		_attrs.update({style: style});
		_update();
	}

	/*
	 * Function: getAttributes
	 * Returns tag's attributes
	 *
	 * Return:
	 *  attributes - object: <_attrs> object
	 *
	 */ 
	this.getAttributes = function() {
		return _attrs;
	}

	/*
	 * Function: _main
	 * Entry point
	 *
	 */ 
	function _main() {
		_container = $(container);
		if (!container) {
			throw "Please supply a valid DOM container!";
			return;
		}

		_root = new Element('div').addClassName('tagwidget');
		_container.insert(_root);
		_reset();
	}

	_main();
}
