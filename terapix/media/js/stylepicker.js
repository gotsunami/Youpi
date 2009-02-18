/*
 * Class: StylePicker
 * Widget implementing CSS style selection
 *
 * For convenience, private data member names (both variables and functions) start with an underscore.
 *
 * Constructor Parameters:
 *
 * container - string or DOM object: name of parent DOM block container
 *
 * Custom Events:
 *  stylepicker:styleChanged - signal emitted when the picker's CSS style has changed
 *
 */
function StylePicker(container) {
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
	 * Var: _id
	 * Internal id
	 *
	 */
	var _id = 'stylepicker_';
	/*
	 * Var: _content
	 * content DOM container
	 *
	 */
	var _content;
	/*
	 * Var: _colors
	 * Web 2.0 standard colors
	 *
	 */
	var _colors = [	'#EEEEEE', '#FFFFFF', '#F9F7ED', '#FFFF88', '#CDEB8B', '#C3D9FF', '#36393D', // Neutrals
					'#FF1A00', '#CC0000', '#FF7400', '#008C00', '#006E2E', '#4096EE', '#FF0084', // Bold
					'#B02B2C', '#D15600', '#C79810', '#73880A', '#6BBA70', '#3F4C6B', '#356AA0', // Muted
					'#D01F3C', 'brown',   'transparent' ];


	// Group: Variables
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Var: _attrs
	 * Style attributes
	 *
	 */
	var _attrs = ['Text', 'Background', 'Border'];
	/*
	 * Var: _context
	 * Current CSS context (one of <_attrs>) 
	 *
	 */
	var _context = _attrs[1];


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
	}

	/*
	 * Function: getStyle
	 * Returns CSS style 
	 *
	 * Returns:
	 *  string - Raw CSS style
	 *
	 */ 
	this.getStyle = function() {
		return 	'background-color: ' + _root.getStyle('backgroundColor') + 
				'; color:' + _root.getStyle('color') +
				'; border:' + _root.getStyle('border') + ';';
	}

	/*
	 * Function: setStyle
	 * Sets picker CSS style 
	 *
	 * Parameters:
	 *  string - Raw CSS style
	 *
	 */ 
	this.setStyle = function(style) {
		if(typeof style != 'string') {
			throw 'setStyle: style must be a CSS string';
			return;
		}

		_root.writeAttribute('style', style);
		// Emit signal
		document.fire('stylePicker:styleChanged');
	}

	/*
	 * Function: _renderContent
	 * Renders content widget (CSS properties)
	 *
	 */ 
	function _renderContent() {
		_content = new Element('div').hide();

		var lks = _attrs.map(function(attr) {
			return new Element('a', {href: '#'}).update(attr).observe('click', function() {
				_content.select('a').each(function(link) {
					link.removeClassName('context');
				});
				if (!this.hasClassName('context'))
					this.addClassName('context');

				// Set context
				_context = attr;
			});
		});

		var d = new Element('div');
		lks.each(function(link) { 
			d.insert(new Element('span', {style: 'padding-right: 5px'}).update(link)); 
			// Turn on default context
			if (link.innerHTML == _context)
				link.addClassName('context');
		});
		d.insert('<br/>');

		var zd = new Element('div', {style: 'margin-top: 2px;'});
		var t = new Element('table').addClassName('palette');
		var tr, td, colp;
		var cols = 7;
		var j = 0;

		tr = new Element('tr');
		t.insert(tr);
		_colors.each(function(col) {
			if (j > cols) {
				tr = new Element('tr');
				t.insert(tr);
				j = 0;
			}
			td = new Element('td');
			colp = new ColorPicker(td, col);
			tr.insert(td);
			j++;
		});

		zd.insert(t);
		d.insert(zd);
		_content.insert(d);
		_container.insert(_content);
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

		_root = new Element('div').addClassName('stylepicker');
		_root.observe('click', function() {
			new Effect.toggle(_content, 'slide');
		});
		_root.setStyle({backgroundColor: 'brown', border: 'none', color: 'white'});
		_root.update('a');
		_container.insert(_root);

		_renderContent();

		// Custom slots
		document.observe('colorPicker:clicked', function(event) {
			var s;
			switch(_context) {
				case 'Border':
					s = {border: '1px solid ' + event.memo.color};
					break;
				case 'Background':
					s = {backgroundColor: event.memo.color};
					break;
				case 'Text':
					s = {color: event.memo.color};
					break;
				default:
					break;
			}
			_root.setStyle(s);

			// Emit signal
			document.fire('stylePicker:styleChanged');
		});
	}

	_main();
}

/*
 * Class: ColorPicker
 * Widget implementing a single color picker
 *
 * For convenience, private data member names (both variables and functions) start with an underscore.
 *
 * Constructor Parameters:
 *  container - string or DOM object: name of parent DOM block container
 *  bgcolor - string: background color name
 *
 * Custom Events:
 *  colorPicker:clicked - signal emitted when the color picker is clicked
 *
 */
function ColorPicker(container, bgcolor) {
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
	 * Var: _bgcolor
	 * Background color
	 *
	 */
	var _bgcolor;


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

		if (typeof bgcolor != 'string') {
			throw "bgcolor must be a valid CSS color name";
			return;
		}

		_bgcolor = bgcolor;
		_root = new Element('div').addClassName('colorpicker').setStyle({backgroundColor: _bgcolor, border: '1px solid black'});

		// Events
		_root.observe('click', function() {
			document.fire('colorPicker:clicked', {color: _bgcolor});
		});
		_root.observe('mouseover', function() {
			this.setStyle({border: '1px solid orange'});
		});
		_root.observe('mouseout', function() {
			this.setStyle({border: '1px solid black'});
		});

		_container.insert(_root);
	}

	_main();
}
