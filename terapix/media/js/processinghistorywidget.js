/*
 * Class: ProcessingHistoryWidget
 * Widget displaying processing history
 *
 * Note:
 *
 * Please note that this page documents Javascript code. <CondorPanel> is a pseudo-class, 
 * it provides encapsulation and basic public/private features.
 *
 * Constructor Parameters:
 *
 * container - string or DOM node: name of parent DOM block container
 * varName - string: global variable name of instance, used internally for public interface definition
 *
 * Requires:
 *  - <getSelect> for DOM select facilities
 *
 */
function ProcessingHistoryWidget(container, varName) {
	// Group: Constants
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Var: _instance_name
	 * Name of instance in global namespace
	 *
	 */
	var _instance_name = varName;
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
		var tab = document.createElement('table');
		tab.setAttribute('class', 'fileBrowser');
		tab.setAttribute('style', 'width: 450px;');

		var th, tr, td;
		// TR title
		tr = document.createElement('tr');
		th = document.createElement('th');
		th.appendChild(document.createTextNode(_headerTitle));
		tr.appendChild(th);
		tab.appendChild(tr);


		// TR input text filtering
		tr = document.createElement('tr');
		td = document.createElement('td');
		var rtab = document.createElement('table');
		rtab.setAttribute('class', 'results-filter');
		var rtr, rtd;
		rtr = document.createElement('tr');
		rtd = document.createElement('td');

		var img = document.createElement('img');
		img.setAttribute('src', '/media/themes/' + guistyle + '/img/admin/selector-search.gif');
		rtd.appendChild(img);

		var input = document.createElement('input');
		input.setAttribute('id', _instance_name + '_filter_text');
		input.setAttribute('type', 'text');
		input.setAttribute('title', 'Press Enter to filter tasks');
		input.setAttribute('onkeyup', 'return ' + _instance_name + '.filterOnKeyUp(event);');
		input.setAttribute('size', '40');
		rtd.appendChild(input);

		img = document.createElement('img');
		img.setAttribute('src', '/media/themes/' + guistyle + '/img/misc/reset.png');
		img.setAttribute('title', 'Reset field');
		img.setAttribute('style', 'cursor: pointer;');
		img.setAttribute('onclick', _instance_name + '.resetFilterText();');
		rtd.appendChild(img);
		rtr.appendChild(rtd);

		rtd = document.createElement('td');
		img = document.createElement('img');
		img.setAttribute('src', '/media/themes/' + guistyle + '/img/admin/icon_success.gif');
		var span = document.createElement('span');
		span.setAttribute('id', _instance_name + '_success_span');
		rtd.appendChild(img);
		rtd.appendChild(span);
		img = document.createElement('img');
		img.setAttribute('src', '/media/themes/' + guistyle + '/img/admin/icon_error.gif');
		span = document.createElement('span');
		span.setAttribute('id', _instance_name + '_failed_span');
		rtd.appendChild(img);
		rtd.appendChild(span);

		rtd.appendChild(document.createTextNode(' ('));
		span = document.createElement('span');
		span.setAttribute('id', _instance_name + '_total_span');
		rtd.appendChild(span);
		rtd.appendChild(document.createTextNode('/'));
		span = document.createElement('span');
		span.setAttribute('id', _instance_name + '_big_total_span');
		rtd.appendChild(span);
		rtd.appendChild(document.createTextNode(')'));
		rtr.appendChild(rtd);

		rtab.appendChild(rtr);
		td.appendChild(rtab);
		tr.appendChild(td);
		tab.appendChild(tr);


		// TR combos filtering
		rtr = document.createElement('tr');
		rtd = document.createElement('td');
		rtd.setAttribute('class', 'filter');
		rtd.setAttribute('nowrap', 'nowrap');
		rtd.setAttribute('colspan', '2');
		var form = document.createElement('form');
		rtd.appendChild(form);

		img = document.createElement('img');
		img.setAttribute('src', '/media/themes/' + guistyle + '/img/16x16/filter.png');
		var label = document.createElement('label');
		label.appendChild(document.createTextNode('Show'));
		form.appendChild(img);
		form.appendChild(label);

		var sel = getSelect(_instance_name + '_owner_select', _sel_owner_options);
		sel.setAttribute('onchange', _instance_name + '.applyFilter();');
		form.appendChild(sel);

		sel = getSelect(_instance_name + '_status_select', _sel_status_options);
		sel.setAttribute('onchange', _instance_name + '.applyFilter();');
		sel.options[sel.options.length-1].setAttribute('selected', 'selected');
		form.appendChild(sel);

		sel = document.createElement('select');
		sel.setAttribute('id', _instance_name + '_kind_select');
		sel.setAttribute('onchange', _instance_name + '.applyFilter();');
		for (var k=0; k < _pluginInfos.length; k++) {
			opt = document.createElement('option');
			if (k == 0)
				opt.setAttribute('selected', 'selected');
			opt.setAttribute('value', _pluginInfos[k][0]);
			opt.appendChild(document.createTextNode(_pluginInfos[k][1] + ' processings'));
			sel.appendChild(opt);
		}
		form.appendChild(sel);

		img = document.createElement('img');
		img.setAttribute('src', '/media/themes/' + guistyle + '/img/misc/reset.png');
		img.setAttribute('title', 'Reset filter');
		img.setAttribute('style', 'cursor: pointer;');
		img.setAttribute('onclick', 'this.parentNode.reset(); ' + _instance_name + ".applyFilter(); document.getElementById('" 
			+ _instance_name + "_filter_text').focus();");
		form.appendChild(img);

		rtr.appendChild(rtd);
		rtab.appendChild(rtr);

		// Pages div
		var pdiv = document.createElement('div');
		pdiv.setAttribute('id', _instance_name + '_pages_div');
		pdiv.setAttribute('class', 'pagination');
		td.appendChild(pdiv);

		// Results div
		var rdiv = document.createElement('div');
		rdiv.setAttribute('id', _instance_name + '_tasks_div');
		rdiv.setAttribute('style', 'border-top: 1px #5b80b2 solid; height: 400px; overflow: auto;');
		td.appendChild(rdiv);

		_container.appendChild(tab);

		// Set focus
		document.getElementById(_instance_name + '_filter_text').focus();
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
	 * Function: resetFilterText
	 * Resets (empty) filter text
	 *
	 */ 
	this.resetFilterText = function() {
		var t = document.getElementById(_instance_name + '_filter_text');
		t.value = '';
		_applyFilter(); 
		t.focus();
	} 

	/*
	 * Function: filterOnLeyUp
	 * KeyUp event handler for filter text line
	 *
	 * Used to monitor whether the return key has been pressed.
	 *
	 * Parameters:
	 *  event - JS event
	 *
	 */ 
	this.filterOnKeyUp = function(event) {
		var filter = document.getElementById(_instance_name + '_filter_text');
		// Return key pressed ?
		if (event.which == 13) {
			_applyFilter();
		}
		return true;
	}

	/*
	 * Function: _applyFilter
	 * Sends AJAX query along with search criterias; show results
	 *
	 */ 
	function _updatePagesNavigation(curPage, pageCount) {
		var pdiv = document.getElementById(_instance_name + '_pages_div');
		pdiv.innerHTML = '';
		pdiv.appendChild(document.createTextNode('Page '));

		if (curPage > 1) {
			a = document.createElement('a');
			a.setAttribute('src', '#');
			a.setAttribute('title', 'Show page ' + (curPage-1));
			a.setAttribute('onclick', _instance_name + ".applyFilter(" + (curPage-1) + ");");
			a.appendChild(document.createTextNode('<'));
			pdiv.appendChild(a);
		}

		if (pageCount < 6) {
			for (var k=1; k <= pageCount; k++) {
				if (curPage == k) {
					var p = document.createElement('span');
					p.appendChild(document.createTextNode(k));
					pdiv.appendChild(p);
				}
				else {
					var a = document.createElement('a');
					a.setAttribute('src', '#');
					a.setAttribute('onclick', _instance_name + ".applyFilter(" + k + ");");
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
				a = document.createElement('a');
				a.setAttribute('src', '#');
				a.setAttribute('onclick', _instance_name + ".applyFilter('1');");
				a.appendChild(document.createTextNode('1'));
				pdiv.appendChild(a);
				// ...
				pdiv.appendChild(document.createTextNode(' ... '));
			}
			if (curPage > 1) {
				// Before
				step = curPage-surroundPageCount > 0 ? curPage-surroundPageCount : curPage-1;
				for (var k=step; k < curPage; k++) {
					a = document.createElement('a');
					a.setAttribute('src', '#');
					a.setAttribute('onclick', _instance_name + ".applyFilter(" + k + ");");
					a.appendChild(document.createTextNode(k));
					pdiv.appendChild(a);
				}
			}
			var p = document.createElement('span');
			p.appendChild(document.createTextNode(curPage));
			pdiv.appendChild(p);
			if (curPage < pageCount) {
				// After
				step = curPage <= (pageCount-surroundPageCount) ? curPage+surroundPageCount : curPage + 1;
				for (var k=curPage+1; k <= step; k++) {
					a = document.createElement('a');
					a.setAttribute('src', '#');
					a.setAttribute('onclick', _instance_name + ".applyFilter(" + k + ");");
					a.appendChild(document.createTextNode(k));
					pdiv.appendChild(a);
				}
			}
			if (curPage < pageCount-2) {
				// ...
				pdiv.appendChild(document.createTextNode(' ... '));
				// Last page
				a = document.createElement('a');
				a.setAttribute('src', '#');
				a.setAttribute('onclick', _instance_name + ".applyFilter(" + pageCount + ");");
				a.appendChild(document.createTextNode(pageCount));
				pdiv.appendChild(a);
			}
		}

		if (curPage < pageCount) {
			a = document.createElement('a');
			a.setAttribute('src', '#');
			a.setAttribute('title', 'Show page ' + (curPage+1));
			a.setAttribute('onclick', _instance_name + ".applyFilter(" + (curPage+1) + ");");
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
			var ownerSel = document.getElementById(_instance_name + '_owner_select');
			var statusSel = document.getElementById(_instance_name + '_status_select');
			var kindSel = document.getElementById(_instance_name + '_kind_select');
			var filter = document.getElementById(_instance_name + '_filter_text');
		} catch(e) { return false; }

		if (!pageNum || typeof pageNum != 'number')
			pageNum = 1;
	
		var owner = ownerSel.options[ownerSel.selectedIndex].text;
		var status = statusSel.options[statusSel.selectedIndex].text;
		var kind = kindSel.options[kindSel.selectedIndex].value;
		var filterText = filter.value;
	
		var container = document.getElementById(_instance_name + '_tasks_div');
		var xhr = new HttpRequest(
			container.id,
			null, // Use default error handler
			// Custom handler for results
			function(resp) {
				var r = resp['results'];
				var st = resp['Stats'];

				// Display pages
				_updatePagesNavigation(st['curPage'], st['pageCount']);

				// Display results
				container.innerHTML = '';
				var len = r.length;
				var tab = document.createElement('table');
				tab.setAttribute('class', 'results');
	
				var tr, td, cls, stab, str, std, d, img, gdiv;
	
				if (status == 'failed' && len && kind != 'all') {
					var rdiv = document.createElement('div');
					rdiv.setAttribute('id', 'reprocess_failed_div');
					rdiv.setAttribute('class', 'reprocess');
					var rimg = document.createElement('img');
					rimg.setAttribute('onclick', kind + "_reprocess_all_failed_processings('" + resp['Stats']['TasksIds'] + "');");
					rimg.setAttribute('src', '/media/themes/' + guistyle + '/img/misc/reprocess.gif');
					rdiv.appendChild(rimg);
					rdiv.appendChild(document.createTextNode(' that current selection of processings that never succeeded'));
					container.appendChild(rdiv);
				}
	
				// Updates stats
				var spans = ['success', 'failed', 'total', 'big_total'];
				for (var k=0; k < spans.length; k++) {
					var node = document.getElementById(_instance_name + '_' + spans[k] + '_span');
					node.innerHTML = '';
					node.appendChild(document.createTextNode(resp['Stats']['nb_' + spans[k]]));
				}
	
				if (!len) {
					tr = document.createElement('tr');	
					td = document.createElement('td');	
					td.setAttribute('style', 'color: grey; cursor: default;');
					td.innerHTML = '<h2>No results found.</h2>';
					tr.appendChild(td);
					tab.appendChild(tr);
					container.appendChild(tab);
					return;
				}
	
				for (var k=0; k < len; k++) {
					cls = r[k]['Success'] ?'success' : 'failure';
					tr = document.createElement('tr');	
					tr.setAttribute('id', 'res_' + r[k]['Id']);
					tr.setAttribute('class', cls);
					tr.setAttribute('onmouseover', "this.setAttribute('class', 'mouseover_" + cls + "');");
					tr.setAttribute('onmouseout', "this.setAttribute('class', '" + cls + "');");
					tr.setAttribute('onclick', "results_showDetails('" + r[k]['Name'] + "'," + r[k]['Id'] + ", true);");
					tab.appendChild(tr);
	
					// Description
					td = document.createElement('td');	
					td.innerHTML = r[k]['Title'];
					d = document.createElement('div');	
					td.appendChild(d);
					tr.appendChild(td);
	
					// Misc info
					stab = document.createElement('table');
					str = document.createElement('tr');	
	
					std = document.createElement('td');	
					std.setAttribute('nowrap', 'nowrap');
					gdiv = document.createElement('div');	
					gdiv.setAttribute('class', 'user');
					gdiv.appendChild(document.createTextNode(r[k]['User']));
					std.appendChild(gdiv);
	
					gdiv = document.createElement('div');	
					gdiv.setAttribute('class', 'node');
					gdiv.appendChild(document.createTextNode(r[k]['Node']));
					std.appendChild(gdiv);
					str.appendChild(std);
	
					std = document.createElement('td');	
					std.setAttribute('nowrap', 'nowrap');
					gdiv = document.createElement('div');	
					gdiv.setAttribute('class', 'clock');
					gdiv.appendChild(document.createTextNode(r[k]['Start']));
					gdiv.appendChild(document.createElement('br'));
					gdiv.appendChild(document.createTextNode(r[k]['Duration'] + ' sec'));
					std.appendChild(gdiv);
					str.appendChild(std);
	
					std = document.createElement('td');	
					std.setAttribute('class', 'exit');
					str.appendChild(std);

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
			var cont = document.getElementById(container);
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
