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
 * Class: ProgressBar
 * ProgressBar widget
 *
 * External Dependancies:
 *  prototype.js - Enhanced Javascript library
 *  scriptaculous.js - Visual effects library
 *
 * Constructor Parameters:
 *  container - string or DOM node: name of parent DOM block container
 *  percent - integer: initial percentage
 *  options - object: options (optional)
 *
 * Available options:
 *  color - string: bar color
 *  borderColor - string: box border color
 *  caption - boolean: display caption [default: true]
 *  animate - boolean: use animation to render [default: true]
 *  width - integer: progress bar's width
 *  height - integer: progress bar's height
 *  captionClassName - string: CSS class name for caption title
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
	 * Var: _options
	 * Default options
	 *
	 */
	var _options = $H({
		color: 'green',
		borderColor: 'green',
		caption: true,
		animate: true,
		width: 100,
		height: 9,
		captionClassName: 'caption'
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
		_percent = pourcent;
		_render(); // Update
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
		return _percent;
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
			height: _options.get('height') + 'px',
			width: _options.get('width') + 'px',
			borderColor: _options.get('borderColor')
		});

		var d = new Element('div').addClassName('bar');
		d.setStyle({
			left: '0px',
			width: '0px',
			height: _options.get('height') + 'px',
			backgroundColor: _options.get('color')
		});

		// Caption div
		if (_options.get('caption')) {
			var cd = new Element('div')
				.setStyle({lineHeight: _options.get('height') + 'px'})
				.addClassName(_options.get('captionClassName'));
			cd.update((Math.round(_percent*10)/10) + '%');
		}

		_container.insert(d).insert(cd);

		if (_options.get('animate')) {
			new Effect.Morph(d, {
				style: { width: (_percent * _options.get('width') / 100) + 'px' },
				duration: 2.0
			});
		}
		else {
			d.setStyle({
				width: (_percent * _options.get('width') / 100) + 'px'
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
