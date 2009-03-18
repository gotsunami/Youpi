/*
 * Class: ProgressBar
 * ProgressBar widget
 *
 * Constructor Parameters:
 *  container - string or DOM node: name of parent DOM block container
 *  percent - integer: initial percentage
 *  options - object: options (optional)
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
	var _height = 9;
	/*
	 * Var: _options
	 * Options
	 *
	 * Allowed options:
	 *  color - string: bar color
	 *  borderColor - string: box border color
	 *  caption - boolean: display caption [default: true]
	 *  animate - boolean: use animation to render [default: true]
	 *
	 */
	var _options = $H({
		color: 'green',
		borderColor: 'green',
		caption: true,
		animate: true
	});


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
	 * Function: setOptions
	 * Sets options
	 *
	 * Parameters:
	 *  options - object
	 *
	 */ 
	this.setOptions = function(options) {
		if (typeof options != 'object') 
			throw 'options must be a valid object';
		_options = _options.merge(options);
		// Update
		_render();
	}

	/*
	 * Function: getOptions
	 * Returns current options
	 *
	 * Returns:
	 *  object - current pb options
	 *
	 */ 
	this.getOptions = function() {
		return _options;
	}

	/*
	 * Function: getPourcentage
	 * Returns current pourcentage
	 *
	 * Returns:
	 *  number - current pourcentage
	 *
	 */ 
	this.getPourcentage = function() {
		return _pourcent;
	}

	/*
	 * Function: _render
	 * Renders widget
	 *
	 */ 
	function _render() {
		_container.update();
		_container.addClassName('youpi_progressBar');
		_container.setStyle({
			height: _height + 'px', 
			width: _width + 'px', 
			borderColor: _options.get('borderColor')
		});

		var d = new Element('div').addClassName('bar');
		d.setStyle({
			left: '0px',
			width: '0px',
			height: _height + 'px', 
			backgroundColor: _options.get('color')
		});

		// Caption div
		if (_options.get('caption')) {
			var cd = new Element('div').addClassName('caption');
			cd.update((Math.round(_percent*10)/10) + '%');
		}

		_container.insert(d).insert(cd);

		if (_options.get('animate')) {
			new Effect.Morph(d, {
				style: { width: (_percent * _width / 100) + 'px' },
				duration: 2.0
			});
		}
		else {
			d.setStyle({
				width: (_percent * _width / 100) + 'px'
			});
		}
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
		if (options) {
			if (typeof options != 'object') 
				throw 'options must be a valid object';
			_options = _options.merge(options);
		}
		_percent = percent;
		_render();
	}

	_main();
}
