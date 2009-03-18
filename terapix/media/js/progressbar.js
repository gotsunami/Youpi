/*
 * Class: ProgressBar
 * ProgressBar widget
 *
 * Constructor Parameters:
 *  container - string or DOM node: name of parent DOM block container
 *  percent - integer: initial percentage
 *  options - object: options
 *
 */
function ProgressBar(container, percent, options) {
	// Group: Constants
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Var: _container
	 * Parent DOM container
	 *
	 */ 
	var _container;
	/*
	 * Var: _percent
	 * Current internal percentage
	 *
	 */ 
	var _percent;


	// Group: Variables
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Var: _width
	 * Progress bar's width
	 *
	 */
	var _width = 100;
	/*
	 * Var: _height
	 * Progress bar's height
	 *
	 */
	var _height = 8;
	/*
	 * Var: _bgcolor
	 * Progress bar's background color
	 *
	 */
	var _bgcolor = 'green';


	// Group: Functions
	// -----------------------------------------------------------------------------------------------------------------------------

	/*
	 * Function: setPourcentage
	 * Sets current pourcentage
	 *
	 * Parameters:
	 *  percent - integer: percentage (max 100)
	 *
	 */ 
	this.setPourcentage = function(pourcent) {
		_pourcent = pourcent;

		// Update
		_render();
	}

	/*
	 * Function: getContainer
	 * Return widget parent container
	 *
	 * Returns:
	 *  DOM container
	 *
	 */ 
	this.getContainer = function() {
		return _container;
	}

	/*
	 * Function: _render
	 * Renders widget
	 *
	 */ 
	function _render() {
		_container.update();
		_container.addClassName('youpi_progressBar');

		var d = new Element('div').addClassName('bar');
		d.setStyle({
			left: (_percent * _width / 100 - _width) + 'px', 
			width: _width + 'px', 
			height: _height + 'px', 
			backgroundColor: _bgcolor
		});
		_container.insert(d);
	}

	/*
	 * Function: _main
	 * MEP
	 *
	 */ 
	function _main() {
		_container = $(container);
		if (!container)
			throw 'container must be a valid DOM container';
		if (typeof percent != 'number') 
			throw 'percent must be a valid number';

		_percent = percent;
		_render();
	}

	_main();
}
