/*
 * Class: TagWidget
 * Widget implementing tags
 *
 * Private data member names (both variables and functions) start with an underscore.
 *
 * Constructor Parameters:
 *  container - string or DOM object: name of parent DOM block container
 *
 * Custom Events:
 *  tagWidget:edit - signal emitted when a tag is double-clicked and the widget is set editable (See <setEditable>)
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
	/*
	 * Var: _dragNDropEnabled
	 * True if drag'n drop enabled (default: false)
	 *
	 */
	var _dragNDropEnabled = false;
	/*
	 * Var: _editable
	 * True if widget is editable (default: false)
	 *
	 * Note:
	 *  If true, a tagWidget:edit signal is sent with tag attributes as parameter
	 *
	 */
	var _editable = false;
	/*
	 * Var: _drag
	 * Draggable instance (default: null)
	 *
	 */
	var _drag = null;


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
		_setName(name);
	}

	/*
	 * Function: _setName
	 * Sets tag name
	 *
	 */ 
	function _setName(name) {
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
			comment: null,
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
	 * Function: setComment
	 * Sets tag comment
	 *
	 * Parameters:
	 *  msg - string
	 *
	 */ 
	this.setComment = function(msg) {
		if (typeof msg != 'string') {
			throw "setComment expects a string!";
			return;
		}

		_attrs.update({comment: msg});
	}

	/*
	 * Function: setOwner
	 * Sets tag owner
	 *
	 * Parameters:
	 *  owner - string
	 *
	 */ 
	this.setOwner = function(owner) {
		if (typeof owner != 'string') {
			throw "setOwner expects a string!";
			return;
		}

		_attrs.update({owner: owner});
	}

	/*
	 * Function: setCreationDate
	 * Sets tag creation date
	 *
	 * Parameters:
	 *  date - string
	 *
	 */ 
	this.setCreationDate = function(date) {
		if (typeof date != 'string') {
			throw "setCreationDate expects a string!";
			return;
		}

		_attrs.update({cdate: date});
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
	 * Function: enableDragNDrop
	 * Enables drag and drop
	 *
	 * Paramters:
	 *  enable - boolean: Enable or Disable drag'n drop
	 *
	 */ 
	this.enableDragNDrop = function(enable) {
		if (typeof enable != 'boolean') {
			throw "enableDragNDrop: must provide a boolean";
			return;
		}

		_dragNDropEnabled = enable;
		if (enable) {
			_root.addClassName('dragndrop');
			_drag = new Draggable(_root, {revert: true});	
		}
		else {
			_root.removeClassName('dragndrop');
			if (_drag) {
				_drag.destroy();
				delete _drag;
				_drag = null;
			}
		}
	}

	/*
	 * Function: setEditable
	 * Sets widget editable
	 *
	 * Parameters:
	 *  enable - boolean: Enable or Disable drag'n drop
	 *
	 * Signals:
	 *  If _enable_ is true, a *tagWidget:edit* signal is sent along with tag attributes as parameter when
	 *  the widget is double-clicked.
	 *
	 */ 
	this.setEditable = function(enable) {
		if (typeof enable != 'boolean') {
			throw "setEditable: must provide a boolean";
			return;
		}

		_editable = enable;
		if (enable) {
			_root.observe('dblclick', function() {
				document.fire('tagWidget:edit', _attrs);
			});
			_root.writeAttribute('title', 'Double click to edit');
		}
		else {
			_root.stopObserving('dblclick');
			_root.writeAttribute('title', '');
		}
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

		_root = new Element('span').addClassName('tagwidget');
		_container.insert(_root);
		_reset();

		if (name)
			_setName(name);
	}

	_main();
}
