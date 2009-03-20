/*
 * Function: swap_display
 * This function activates a link and disables all 'li' elements that 
 * does not match the li_id
 *
 * All divs whose names start with 'menuitem' are hidden too. Only the 
 * element 'div_on' is visible
 *
 */
function swap_display(li_id, div_on, ul_id, div_prefix) {
	var nodeLink = document.getElementById(li_id);
	var nodeTurnOn  = document.getElementById(div_on);
		
	// Hides all div elements whose id starts with div_prefix
	var itemsToHide = document.getElementsByTagName('div');
	for (var i=0; i < itemsToHide.length; i++) {
		if (itemsToHide[i].hasAttribute('id')) {
			if (itemsToHide[i].getAttribute('id').indexOf(div_prefix) == 0) {
				itemsToHide[i].style.display = 'none';
			}
		}
	}

	// Disables all li elements
	var nodeUL = document.getElementById(ul_id);
	for (var i=0; i < nodeUL.childNodes.length; i++) {
		nodeUL.childNodes[i].className = 'disabled';
	}

	// Enables selected li
	nodeLink.parentNode.className = 'enabled';

	// Then show the div block
	nodeTurnOn.style.display = 'block';
	nodeTurnOn.focus();
}

/*
 * Class: SubMenu
 * Creates a sub menu on the page
 *
 * Constructor Parameters:
 *  container - string or DOM object: name of parent DOM block container
 *  entries - object: array of string part of the menu
 *
 * Custom Events:
 *  subMenu:clicked - signal emitted when a submenu item is clicked
 *
 */
function SubMenu(container, entries) {

	// Group: Variables
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Var: _container
	 * DOM node container
	 *
	 */
	var _container = $(container);
	/*
	 * Var: _entries
	 * Menu entries
	 *
	 */
	var _entries = $A(entries);
	/*
	 * Var: _ul
	 * Top-level ul DOM node containing li entries
	 *
	 */
	var _ul;
	/*
	 * Var: _currentIdx
	 * Current activated menu's 0-based index
	 *
	 */
	var _currentIdx;


	// Group: Functions
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Function: activate
	 * Activates a submenu and disables all others
	 *
	 * See <_activate>
	 *
	 */
	this.activate = function(idx) {
		_activate(idx);	
	}

	/*
	 * Function: _activate
	 * Activates a submenu and disables all others
	 *
	 * Parameters:
	 * idx - integer: 0-based item number
	 *
	 * Signal:
	 *  subMenu:clicked with _idx_ as a parameter
	 *
	 */
	function _activate(idx) {
		var lis = $$('ul#menu li');
		lis.each(function(li) {
			li.setAttribute('class', 'disabled');
		});

		if (typeof idx == 'number')
			lis[idx].writeAttribute({'class': 'enabled'});
		else if(typeof idx == 'object') {
			idx.up().writeAttribute({'class': 'enabled'});
			idx = idx.getAttribute('id').gsub(/entry_/, '');
		}
		else
			throw 'idx must be an integer or a LI DOM object';

		var divs = new Array();
		_entries.each(function(entry, j) {
			divs.push($('menuitem_sub_' + j));
		});
		if ($('menuitem_sub_about'))
			divs.push($('menuitem_sub_about'));

		// Deals with divs
		divs.each(function(div) { div.hide(); });
		$('menuitem_sub_' + idx).show();

		_currentIdx = idx;
		document.fire('subMenu:clicked', idx);
	}

	/*
	 * Function: _main
	 * Builds the menu (main entry point)
	 *
	 */
	function _main() {
		_ul = new Element('ul', {'class': 'smart_tabnav_sub', id: 'menu'});
		var li, a;
		_entries.each(function(entry, k) {
			li = new Element('li', {'class': 'disabled'});
			a = new Element('a', {href: '#', id: 'entry_' + k}).update(entry);
			a.observe('click', function() {
				_activate(this);
				// Finally, executes custom handler, if any
				if (this.up().customClickHandler)
					this.up().customClickHandler();
			});
			li.insert(a);
			_ul.insert(li);

			// Setup null custom handlers as default
			_ul.childElements()[k].customClickHandler = null;
		});

		_container.insertBefore(_ul, _container.childElements().first());
		_activate(0);
	}

	/*
	 * Function: getEntry
	 * Returns an LI DOM elemeent
	 *
	 * Parameters:
	 *  idx - integer: entry index
	 *
	 * Returns:
	 *  li DOM node
	 *
	 */
	this.getEntry = function(idx) {
		if (typeof idx != 'number')
			throw 'idx parameter must be an integer!';

		return _ul.childElements()[idx];
	}

	/*
	 * Function: getContentNodeForEntry
	 * Returns div DOM container for one entry
	 *
	 * Parameters:
	 *  li - object: DOM node element
	 *
	 * Returns:
	 *  div DOM node
	 *
	 */
	this.getContentNodeForEntry = function(li) {
		if (typeof li != 'object')
			throw 'li must be a DOM li object!';

		var idx = li.down().id.gsub(/entry_/, '');
		return $('menuitem_sub_' + idx);
	}

	/*
	 * Function: getContentNodeForCurrentEntry
	 * Returns div DOM container for current menu entry
	 *
	 * Returns:
	 *  div DOM node
	 *
	 */
	this.getContentNodeForCurrentEntry = function() {
		return $('menuitem_sub_' + _currentIdx);
	}

	/*
	 * Function: setOnClickHandler
	 * Attaches an handler function to one menu's entry
	 *
	 * Parameters:
	 *  idx - integer: entry index
	 *  handler - function: custom handler
	 *
	 */
	this.setOnClickHandler = function(idx, handler) {
		if (typeof handler != 'function')
			throw 'Handler must be a function!';
		if (typeof idx != 'number')
			throw 'idx parameter must be an integer!';

		// Adds handler to li DOM element
		_ul.childElements()[idx].customClickHandler = handler;
	}

	_main();
}
