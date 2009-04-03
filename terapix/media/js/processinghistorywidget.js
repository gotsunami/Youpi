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
 * Class: ProcessingHistoryWidget
 * Widget displaying processing history
 *
 * External Dependancies:
 *  common.js - <getSelect> function
 *  prototype.js - Enhanced Javascript library
 *
 * Constructor Parameters:
 *  container - string or DOM node: name of parent DOM block container
 *
 */
function ProcessingHistoryWidget(container) {
	// Group: Constants
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Var: _id
	 * Unique instance identifier
	 *
	 */ 
	var _id = 'PHW_' + Math.floor(Math.random() * 999999);
	/*
	 * Var_: headerTitle
	 * Header box's title
	 *
	 */
	var _headerTitle = 'Processing History';
	/*
	 * Var: _container
	 * Parent DOM container
	 *
	 */ 
	var _container;
	/*
	 * Var: _sel_owner_choices
	 * Options titles for owner DOM select
	 *
	 */ 
	var _sel_owner_options = ['all', 'my', 'others'];
	/*
	 * Var: _sel_status_choices
	 * Options titles for status DOM select
	 *
	 */ 
	var _sel_status_options = ['successful', 'failed', 'finished'];


	// Group: Variables
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Var: _pluginInfos
	 * Array or array of string describing plugins (used in combobox)
	 *
	 * Format:
	 *  [['scamp', 'label1'], ...]
	 *
	 */
	var _pluginInfos;
	/*
	 * Var: _maxPerPage
	 * Max number of results per page
	 *
	 */
	var _maxPerPage = 20;


	// Group: Functions
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Function: render
	 * Call this method to render widget
	 *
	 */ 
	this.render = function() {
		_render();
		_applyFilter();
	}

	/*
	 * Function: _render
	 * Main rendering function
	 *
	 */ 
	function _render() {
		var tab = new Element('table');
		tab.setAttribute('class', 'fileBrowser');
		tab.setAttribute('style', 'width: 450px;');

		var th, tr, td;
		// TR title
		tr = new Element('tr');
		th = new Element('th');
		th.appendChild(document.createTextNode(_headerTitle));
		tr.appendChild(th);
		tab.appendChild(tr);


		// TR input text filtering
		tr = new Element('tr');
		td = new Element('td');
		var rtab = new Element('table');
		rtab.setAttribute('class', 'results-filter');
		var rtr, rtd;
		rtr = new Element('tr');
		rtd = new Element('td');

		var img = new Element('img');
		img.setAttribute('src', '/media/themes/' + guistyle + '/img/admin/selector-search.gif');
		rtd.appendChild(img);

		var input = new Element('input');
		input.setAttribute('id', _id + '_filter_text');
		input.setAttribute('type', 'text');
		input.setAttribute('title', 'Press Enter to filter tasks');
		input.observe('keyup', function(event) {
			return _filterOnKeyUp(event);
		});

		input.setAttribute('size', '40');
		rtd.appendChild(input);

		img = new Element('img');
		img.setAttribute('src', '/media/themes/' + guistyle + '/img/misc/reset.png');
		img.setAttribute('title', 'Reset field');
		img.setAttribute('style', 'cursor: pointer;');
		img.observe('click', function() {
			_resetFilterText();
		});
		rtd.appendChild(img);
		rtr.appendChild(rtd);

		rtd = new Element('td');
		img = new Element('img');
		img.setAttribute('src', '/media/themes/' + guistyle + '/img/admin/icon_success.gif');
		var span = new Element('span');
		span.setAttribute('id', _id + '_success_span');
		rtd.appendChild(img);
		rtd.appendChild(span);
		img = new Element('img');
		img.setAttribute('src', '/media/themes/' + guistyle + '/img/admin/icon_error.gif');
		span = new Element('span');
		span.setAttribute('id', _id + '_failed_span');
		rtd.appendChild(img);
		rtd.appendChild(span);

		rtd.appendChild(document.createTextNode(' ('));
		span = new Element('span');
		span.setAttribute('id', _id + '_total_span');
		rtd.appendChild(span);
		rtd.appendChild(document.createTextNode('/'));
		span = new Element('span');
		span.setAttribute('id', _id + '_big_total_span');
		rtd.appendChild(span);
		rtd.appendChild(document.createTextNode(')'));
		rtr.appendChild(rtd);

		rtab.appendChild(rtr);
		td.appendChild(rtab);
		tr.appendChild(td);
		tab.appendChild(tr);


		// TR combos filtering
		rtr = new Element('tr');
		rtd = new Element('td');
		rtd.setAttribute('class', 'filter');
		rtd.setAttribute('nowrap', 'nowrap');
		rtd.setAttribute('colspan', '2');
		var form = new Element('form');
		rtd.appendChild(form);

		img = new Element('img');
		img.setAttribute('src', '/media/themes/' + guistyle + '/img/16x16/filter.png');
		var label = new Element('label');
		label.appendChild(document.createTextNode('Show'));
		form.appendChild(img);
		form.appendChild(label);

		var sel = getSelect(_id + '_owner_select', _sel_owner_options);
		sel.observe('change', function() {
			_applyFilter();
		});
		form.appendChild(sel);

		sel = getSelect(_id + '_status_select', _sel_status_options);
		sel.observe('change', function() {
			_applyFilter();
		});
		sel.options[sel.options.length-1].setAttribute('selected', 'selected');
		form.appendChild(sel);

		sel = new Element('select');
		sel.setAttribute('id', _id + '_kind_select');
		sel.observe('change', function() {
			_applyFilter();
		});
		for (var k=0; k < _pluginInfos.length; k++) {
			opt = new Element('option');
			if (k == 0)
				opt.setAttribute('selected', 'selected');
			opt.setAttribute('value', _pluginInfos[k][0]);
			opt.appendChild(document.createTextNode(_pluginInfos[k][1] + ' processings'));
			sel.appendChild(opt);
		}
		form.appendChild(sel);

		img = new Element('img');
		img.setAttribute('src', '/media/themes/' + guistyle + '/img/misc/reset.png');
		img.setAttribute('title', 'Reset filter');
		img.setAttribute('style', 'cursor: pointer;');
		img.observe('click', function() {
			this.parentNode.reset();
			_applyFilter();
			$(_id + '_filter_text').focus();
		});
		form.appendChild(img);

		rtr.appendChild(rtd);
		rtab.appendChild(rtr);

		// Pages div
		var pdiv = new Element('div', {id: _id + '_pages_div'}).addClassName('pageSwitcher');
		td.insert(pdiv);

		// Results div
		var rdiv = new Element('div');
		rdiv.setAttribute('id', _id + '_tasks_div');
		rdiv.setAttribute('style', 'border-top: 1px #5b80b2 solid; height: 400px; overflow: auto;');
		td.appendChild(rdiv);

		_container.appendChild(tab);

		// Set focus
		$(_id + '_filter_text').focus();
	}

	/*
	 * Function: setActivePlugins
	 * Defines list of current active plugins
	 *
	 * Required to set up processing types (filtering options)
	 *
	 * See Also:
	 *  <_pluginsInfos> for format definition
	 *
	 */ 
	this.setActivePlugins = function(plugInfo) {
		_pluginInfos = plugInfo;
	}

	/*
	 * Function: _resetFilterText
	 * Resets (empty) filter text
	 *
	 */ 
	function _resetFilterText() {
		var t = $(_id + '_filter_text');
		t.value = '';
		_applyFilter(); 
		t.focus();
	} 

	/*
	 * Function: _filterOnKeyUp
	 * KeyUp event handler for filter text line
	 *
	 * Used to monitor whether the return key has been pressed.
	 *
	 * Parameters:
	 *  event - JS event
	 *
	 */ 
	function _filterOnKeyUp(event) {
		var filter = $(_id + '_filter_text');
		// Return key pressed ?
		if (event.which == 13) {
			_applyFilter();
		}
		return true;
	}

	/*
	 * Function: _updatePagesNavigation
	 * Updates page navigator
	 *
	 */ 
	function _updatePagesNavigation(curPage, pageCount) {
		var pdiv = $(_id + '_pages_div');
		pdiv.innerHTML = '';
		pdiv.appendChild(document.createTextNode('Page '));

		if (curPage > 1) {
			a = new Element('a');
			a.setAttribute('src', '#');
			a.setAttribute('title', 'Show page ' + (curPage-1));
			a.pdata = curPage - 1;
			a.observe('click', function() {
				_applyFilter(this.pdata);
			});
			a.appendChild(document.createTextNode('<'));
			pdiv.appendChild(a);
		}

		if (pageCount < 6) {
			for (var k=1; k <= pageCount; k++) {
				if (curPage == k) {
					var p = new Element('span');
					p.appendChild(document.createTextNode(k));
					pdiv.appendChild(p);
				}
				else {
					var a = new Element('a');
					a.setAttribute('src', '#');
					a.pdata = k;
					a.observe('click', function() {
						_applyFilter(this.pdata);
					});
					a.appendChild(document.createTextNode(k));
					pdiv.appendChild(a);
				}
			}
		}
		else {
			var surroundPageCount = 2;
			var step, a;
			if (curPage > surroundPageCount+1) {
				// Last page
				a = new Element('a');
				a.setAttribute('src', '#');
				a.observe('click', function() {
					_applyFilter(1);
				});
				a.appendChild(document.createTextNode('1'));
				pdiv.appendChild(a);
				// ...
				pdiv.appendChild(document.createTextNode(' ... '));
			}
			if (curPage > 1) {
				// Before
				step = curPage-surroundPageCount > 0 ? curPage-surroundPageCount : curPage-1;
				for (var k=step; k < curPage; k++) {
					a = new Element('a');
					a.setAttribute('src', '#');
					a.pdata = k;
					a.observe('click', function() {
						_applyFilter(this.pdata);
					});
					a.appendChild(document.createTextNode(k));
					pdiv.appendChild(a);
				}
			}
			var p = new Element('span');
			p.appendChild(document.createTextNode(curPage));
			pdiv.appendChild(p);
			if (curPage < pageCount) {
				// After
				step = curPage <= (pageCount-surroundPageCount) ? curPage+surroundPageCount : curPage + 1;
				for (var k=curPage+1; k <= step; k++) {
					a = new Element('a');
					a.setAttribute('src', '#');
					a.pdata = k;
					a.observe('click', function() {
						_applyFilter(this.pdata);
					});
					a.appendChild(document.createTextNode(k));
					pdiv.appendChild(a);
				}
			}
			if (curPage < pageCount-2) {
				// ...
				pdiv.appendChild(document.createTextNode(' ... '));
				// Last page
				a = new Element('a');
				a.setAttribute('src', '#');
				a.pdata = pageCount;
				a.observe('click', function() {
					_applyFilter(this.pdata);
				});
				a.appendChild(document.createTextNode(pageCount));
				pdiv.appendChild(a);
			}
		}

		if (curPage < pageCount) {
			a = new Element('a');
			a.setAttribute('src', '#');
			a.setAttribute('title', 'Show page ' + (curPage+1));
			a.pdata = curPage + 1;
			a.observe('click', function() {
				_applyFilter(this.pdata);
			});
			a.appendChild(document.createTextNode('>'));
			pdiv.appendChild(a);
		}
	}

	/*
	 * Function: _applyFilter
	 * Sends AJAX query along with search criterias; show results
	 *
	 */ 
	function _applyFilter(pageNum) {
		try {
			var ownerSel = $(_id + '_owner_select');
			var statusSel = $(_id + '_status_select');
			var kindSel = $(_id + '_kind_select');
			var filter = $(_id + '_filter_text');
		} catch(e) { return false; }

		if (!pageNum || typeof pageNum != 'number')
			pageNum = 1;
	
		var owner = ownerSel.options[ownerSel.selectedIndex].text;
		var status = statusSel.options[statusSel.selectedIndex].text;
		var kind = kindSel.options[kindSel.selectedIndex].value;
		var filterText = filter.value;
	
		var container = $(_id + '_tasks_div');
		var xhr = new HttpRequest(
			container,
			null, // Use default error handler
			// Custom handler for results
			function(resp) {
				var r = resp.results;
				var st = resp.Stats;

				// Display pages
				_updatePagesNavigation(st.curPage, st.pageCount);

				// Display results
				container.update();
				var len = r.length;
				var tab = new Element('table').addClassName('results');
				var tr, td, cls, stab, str, std, d, img, gdiv;
	
				/*
				 * FIXME
				 * reprocess_all_failed_processing is not yet implemented in any plugin...
				 *

				if (status == 'failed' && len && kind != 'all') {
					var rdiv = new Element('div');
					rdiv.setAttribute('id', 'reprocess_failed_div');
					rdiv.setAttribute('class', 'reprocess');
					var rimg = new Element('img');
					rimg.setAttribute('onclick', kind + ".reprocess_all_failed_processings('" + resp['Stats']['TasksIds'] + "');");
					rimg.setAttribute('src', '/media/themes/' + guistyle + '/img/misc/reprocess.gif');
					rdiv.appendChild(rimg);
					rdiv.appendChild(document.createTextNode(' that current selection of processings that never succeeded'));
					container.appendChild(rdiv);
				}
				*/
	
				// Updates stats
				var spans = ['success', 'failed', 'total', 'big_total'];
				for (var k=0; k < spans.length; k++) {
					var node = $(_id + '_' + spans[k] + '_span');
					node.innerHTML = '';
					node.appendChild(document.createTextNode(resp['Stats']['nb_' + spans[k]]));
				}
	
				if (!len) {
					tr = new Element('tr');	
					td = new Element('td');	
					td.setAttribute('style', 'color: grey; cursor: default;');
					td.innerHTML = '<h2>No results found.</h2>';
					tr.appendChild(td);
					tab.appendChild(tr);
					container.appendChild(tab);
					return;
				}
	
				for (var k=0; k < len; k++) {
					cls = r[k]['Success'] ?'success' : 'failure';
					tr = new Element('tr');	
					tr.setAttribute('id', 'res_' + r[k]['Id']);
					tr.setAttribute('class', cls);
					tr.setAttribute('onmouseover', "this.setAttribute('class', 'mouseover_" + cls + "');");
					tr.setAttribute('onmouseout', "this.setAttribute('class', '" + cls + "');");
					tr.setAttribute('onclick', "results_showDetails('" + r[k]['Name'] + "'," + r[k]['Id'] + ", true);");
					tab.appendChild(tr);
	
					// Description
					td = new Element('td');	
					td.innerHTML = r[k]['Title'];
					d = new Element('div');	
					td.appendChild(d);
					tr.appendChild(td);
	
					// Misc info
					stab = new Element('table');
					str = new Element('tr');	
	
					std = new Element('td');	
					std.setAttribute('nowrap', 'nowrap');
					gdiv = new Element('div');	
					gdiv.setAttribute('class', 'user');
					gdiv.appendChild(document.createTextNode(r[k]['User']));
					std.appendChild(gdiv);
	
					gdiv = new Element('div');	
					gdiv.setAttribute('class', 'node');
					gdiv.appendChild(document.createTextNode(r[k]['Node']));
					std.appendChild(gdiv);
					str.appendChild(std);
	
					std = new Element('td');	
					std.setAttribute('nowrap', 'nowrap');
					gdiv = new Element('div');	
					gdiv.setAttribute('class', 'clock');
					gdiv.appendChild(document.createTextNode(r[k]['Start']));
					gdiv.appendChild(new Element('br'));
					gdiv.appendChild(document.createTextNode(r[k]['Duration'] + ' sec'));
					std.appendChild(gdiv);
					str.appendChild(std);
	
					// td.exit could contain per-plugin additionnal data
					std = new Element('td');	
					std.setAttribute('class', 'exit');
					str.appendChild(std);
					if (r[k].Extra) {
						std.update(r[k].Extra);
					}

					stab.appendChild(str);
					d.appendChild(stab);
					tr.appendChild(td);
	
					tab.appendChild(tr);
				}
	
				container.appendChild(tab);
			}
		);
	
		// Checks if a selection of that name already exists
		post = 	'Owner=' + owner + 
				'&Status=' + status + 
				'&Kind=' + kind +
				'&Limit=' + _maxPerPage +
				'&Page=' + pageNum +
				'&FilterText=' + filterText;
	
		// Send HTTP POST request
		xhr.setBusyMsg('Please wait while filtering processing data');
		xhr.send('/youpi/results/filter/', post);
	}

	/*
	 * Function: applyFilter
	 * Public method for <_applyFilter>
	 *
	 */ 
	this.applyFilter = function(pageNum) {
		_applyFilter(pageNum);
	}

	/*
	 * Function: _error
	 * Displays an alert error message
	 *
	 * Parameters:
	 *  msg - string: error message to display
	 *
	 */ 
	function _error(msg) {
		alert('ProcessingHistoryWidget: ' + msg);
	}

	/*
	 * Function: _render
	 * Main rendering function
	 *
	 */ 
	function _main() {
		if (!container) {
			_error("Container is null!");
			return;
		}

		if (typeof container == 'string') {
			var cont = $(container);
			if (!cont) {
				_error('not a valid container: ' + container);
				return;
			}
			_container = cont;
		}
		else if (typeof container == 'object') {
			_container = container;
		}
		else {
			_error('Bad container type: ' + typeof container);
			return;
		}
	}

	_main();
}
