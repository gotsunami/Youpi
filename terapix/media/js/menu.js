/*
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

function SubMenu(container, entries) {
	var _container = $(container);
	var _entries = $A(entries);
	var _ul;

	function _main() {
		_ul = new Element('ul', {'class': 'smart_tabnav_sub', id: 'menu'});
		var li, a;
		_entries.each(function(entry, k) {
			li = new Element('li', {'class': 'disabled'});
			a = new Element('a', {href: '#', id: 'entry_' + k}).update(entry);
			a.observe('click', function() {
				var divs = new Array();
				_entries.each(function(entry, j) {
					divs.push($('menuitem_sub_' + j));
				});
				if ($('menuitem_sub_about'))
					divs.push($('menuitem_sub_about'));

				// Deals with divs
				divs.each(function(div) { div.hide(); });
				$('menuitem_sub_' + k).show();

				// Deals with lis
				var lis = $$('ul#menu li');
				lis.each(function(li) {
					li.setAttribute('class', 'disabled');
				});
				this.up().setAttribute('class', 'enabled');

				// Finally, executes custom handler, if any
				if (this.up().customClickHandler)
					this.up().customClickHandler();
			});
			li.insert(a);
			_ul.insert(li);

			// Setup null custom handlers as default
			_ul.childElements()[k].customClickHandler = null;
		});
		_ul.select('li').first().setAttribute('class', 'enabled');
		_container.insertBefore(_ul, _container.childElements().first());
	}

	this.getEntry = function(idx) {
		if (typeof idx != 'number')
			console.error('idx parameter must be an integer!');

		return _ul.childElements()[idx];
	}

	this.getContentNodeForEntry = function(li) {
		if (typeof li != 'object')
			console.error('li must be a DOM li object!');

		var idx = li.down().id.gsub(/entry_/, '');
		return $('menuitem_sub_' + idx);
	}

	this.setOnClickHandler = function(idx, handler) {
		if (typeof handler != 'function')
			console.error('Handler must be a function!');
		if (typeof idx != 'number')
			console.error('idx parameter must be an integer!');

		// Adds handler to li DOM element
		_ul.childElements()[idx].customClickHandler = handler;
	}

	_main();
}
