/*
 * Class: ImageInfoWidget
 * Widget implementing image information
 *
 * Private data member names (both variables and functions) start with an underscore.
 *
 * Constructor Parameters:
 *  container - string or DOM object: name of parent DOM block container
 *  dbid - string: image DB id
 *
 * Custom Events:
 *  tagWidget:edit - signal emitted when a tag is double-clicked and the widget is set editable (See <setEditable>)
 *
 */
function ImageInfoWidget(container, dbid) {
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
	/*
	 * Var: _body
	 * Inner DOM container
	 *
	 */
	var _body;


	// Group: Variables
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Var: _dbid
	 * string - Image DB id
	 *
	 */
	var _dbid;


	// Group: Functions
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Function: update
	 * Updates widget rendering
	 *
	 */ 
	this.update = function(dbid) {
		_dbid = String(dbid);
		_update();
	}

	/*
	 * Function: _update
	 * Updates widget rendering
	 *
	 */ 
	function _update() {
		var xhr = new HttpRequest(
			_body,
			null,
			// Custom handler for results
			function(resp) {
				if (resp.Error) {
					console.error(resp.Error);
					return;
				}

				_body.update(_dbid);
			}
		);

		var post = {
			Id: _dbid,
		};

		// Send HTTP POST request
		xhr.setBusyMsg('Getting info');
		xhr.send('/youpi/img/info/', $H(post).toQueryString());
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

		_root = new Element('div').addClassName('imageInfoWidget');
		_body = new Element('div');
		_root.insert(_body);
		_container.insert(_root);
	}

	_main();
}
