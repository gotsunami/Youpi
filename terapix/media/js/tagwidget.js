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


	// Group: Variables
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Var: _attrs
	 * Tag's attributes
	 *
	 */
	var _attrs = new Hash();


	// Group: Functions
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Function: _render
	 * Main rendering function
	 *
	 */ 
	function _render() {
		_container = $(container);
		if (!container) {
			throw "Please supply a valid DOM container!";
			return;
		}

		if (!name) {
			_showEditForm(_container);
			return;
		}

		if (typeof name != 'string') {
			throw "Tag name must be a string";
			return;
		}
		_attrs.update({ name: name });

	}

	_render();
}
