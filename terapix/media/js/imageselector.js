
if (!Youpi)
	var Youpi = {};

Youpi.ImageSelector = {};
Youpi.ImageSelector.currentId = 1;

/*
 * Class: ImageSelector
 * Widget that allows image selection.
 *
 * Note:
 *
 * Please note that this page documents Javascript code. <ImageSelector> is a pseudo-class, 
 * it provides encapsulation and basic public/private features.
 *
 * External Dependancies:
 * 
 * This class uses the <Logger> class defined in 
 * : media/js/common.js
 *
 * Constructor Parameters:
 *
 * container_id - string: name of parent DOM block container
 * varName - string: global variable name of instance, used internally for public interface definition
 *
 */
function ImageSelector(container_id, varName)
{
	// Group: Constants
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Var: emptyValueMsg
	 * String for 'empty value' message
	 *
	 */
	var emptyValueMsg = '-- Empty --';
	/*
	 * Var: imgSelRequiredMsg
	 * String message used for error display when no selection of images is available  
	 *
	 */
	var imgSelRequiredMsg = 'Not available until you make an image selection!';
	/*
	 * Var: caption
	 * Widget label
	 *
	 */
	var caption = 'Select among ';
	/*
	 * Var: fields 
	 * List of criteria to choose from to build a query. Each entry will be 
	 * displayed in the first combobox of every added line.
	 *
	 * To get it working, each entry [E] of <fields> must be associated with functions
	 * whose name match:
	 *   - get[E]CondSelect()
	 *   - build[E]DataWidget()
	 *   - get[E]SQLParams()
	 *
	 * Supported search criteria are Run, Object, Instrument, Channel, Name, Ra, Dec, Saved selection and IngestionId.
	 *
	 */
	var fields = 		[	'Run', 'Object', 'Instrument', 'Channel', 'Name', 'Ra', 'Dec', 'Saved', 'IngestionId' ];
	/*
	 * Var: labelFields
	 * Array of labels to use with <fields> entries.
	 *
	 */
	var labelFields = 	[	'Run', 'Object', 'Instrument', 'Channel', 'Image name', 'Ra (deg)', 'Dec (deg)', 'Saved selection', 'Ingestion ID' ];

	var actions = [	'Create a new image selection',
					'Merge saved selections' ];
	/*
	 * Var: _singleMode
	 * Constant for single mode
	 *
	 */ 
	var _singleMode = 0;
	/*
	 * Var: _BatchMode
	 * Constant for batch mode
	 *
	 */ 
	var _batchMode = 1;
	/*
	 * Var: _selectionMode
	 * Current selection mode
	 *
	 */ 
	var _selectionMode = _singleMode;
	/*
	 * Var: _instance_name
	 * Name of instance in global namespace
	 *
	 */ 
	var _instance_name = varName;
	/*
	 * Var: container
	 * Parent DOM container
	 *
	 */ 
	var container = document.getElementById(container_id);
	container.setAttribute('class', 'imageSelector');
	/*
	 * Var: id
	 * Unique instance identifier
	 *
	 */ 
	var id = varName + '_imgSel_' + Youpi.ImageSelector.currentId;
	Youpi.ImageSelector.currentId++;


	// Group: Variables
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Var: _tableWidget
	 * instance - custom table widget for grid rendering
	 *
	 */ 
	var _tableWidget = null;
	/*
	 * Var: _imagesCount;
	 * Integer - total of images selected
	 *
	 */ 
	var _imagesCount = 0;
	/*
	 * Var: _batchModeSelections
	 * Array of current image selections in batch Mode
	 *
	 */ 
	var _batchModeSelections = new Array();
	/*
	 * Var: _singleModeSelections
	 * Array of current image selections in single Mode
	 *
	 * Note:
	 *
	 * This is an array with at most one selection of images (since it is single mode selection)
	 *
	 */ 
	var _singleModeSelections = new Array();
	/*
	 * Var: currentTR
	 * Current row index in HTML table
	 *
	 */ 
	var currentTR = 0;
	/*
	 * Var: topNode
	 * DOM table element
	 *
	 */ 
	var topNode = null;
	/*
	 * Var: idResults
	 * List of matching DB ids from last query
	 *
	 */ 
	var idResults = new Array(); 
	/*
	 * Var: resultHandler
	 * Default result handler
	 *
	 */
	var resultHandler = renderFinalResults;
	/*
	 * Var: selectAllHandler
	 * Default handler for 'Select All' operation
	 *
	 */
	var selectAllHandler = defaultSelectAllHandler;
	/*
	 * Var: unselectAllHandler
	 * Default handler for 'Unselect All' operation
	 *
	 */
	var unselectAllHandler = defaultUnselectAllHandler;
	/*
	 * Var: queryIdx
	 * Index of current query
	 *
	 */
	var queryIdx = 0;
	/*
	 * Var: AIM
	 * 3rd Party GPL'ed code, part of AIM (AJAX IFRAME METHOD)
	 *
	 * See Also:
	 *
	 * <getAIM>, http://www.webtoolkit.info/, <renderBatchSelection>
	 *
	 */ 
	var AIM = {
		frame: function(c) {
			var n = 'f' + Math.floor(Math.random() * 99999);
			var d = document.createElement('DIV');
			d.innerHTML = '<iframe style="display:none" src="about:blank" id="'+n+'" name="'+n+'" onload="' + _instance_name + '.getAIM().loaded(\''+n+'\')"></iframe>';
			document.body.appendChild(d);
	
			var i = document.getElementById(n);
			if (c && typeof(c.onComplete) == 'function') {
				i.onComplete = c.onComplete;
			}
			return n;
		},

		form: function(f, name) {
			f.setAttribute('target', name);
		},

		submit: function(f, c) {
			AIM.form(f, AIM.frame(c));
			if (c && typeof(c.onStart) == 'function') {
				return c.onStart();
			} else {
				return true;
			}
		},

		loaded: function(id) {
			var i = document.getElementById(id);
			if (i.contentDocument) {
				var d = i.contentDocument;
			} else if (i.contentWindow) {
				var d = i.contentWindow.document;
			} else {
				var d = window.frames[id].document;
			}
			if (d.location.href == "about:blank") {
				return;
			}
	
			if (typeof(i.onComplete) == 'function') {
				i.onComplete(d.body.innerHTML);
			}
		}
	}


	// Group: Handler Functions
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Function: _executeHandler
	 * Executes handler
	 *
	 * Parameters:
	 *
	 * tr_idx - integer: index of TR line in table
	 *
	 */ 
	function _executeHandler(tr_idx) {
		var curSelId = document.getElementById(id + '_mainCriteria_select_' + tr_idx);
		var selOption = curSelId.options[curSelId.selectedIndex];

		// Loads matching conditional combo box
		var condDiv = document.getElementById(id + '_cond_div_' + tr_idx);
		var selNode = eval('get' + fields[selOption.value] + 'CondSelect')(tr_idx);
		removeAllChildrenNodes(condDiv);
		condDiv.appendChild(selNode);

		// Now call matching handler
		eval('build' + fields[selOption.value] + 'DataWidget')(tr_idx);
	}

	/*
	 * Function: executeHandler
	 * _Public_ Executes handler, wrapper for the public interface
	 *
	 * Parameters:
	 *
	 * tr_idx - integer: index of TR line in table
	 *
	 */ 
	this.executeHandler = function(tr_idx) {
		_executeHandler(tr_idx);
	}

	/*
	 * Function: setResultHandler
	 * _Public_ Allows to set an alternate result handler
	 *
	 * Parameters:
	 *
	 *  func - function handler
	 *
	 */ 
	this.setResultHandler = function(func) {
		resultHandler = func ? func : renderFinalResults;
	}

	/*
	 * Function: getDefaultResultHandler
	 * _Public_ Gets default result handler
	 *
	 * Parameters:
	 *
	 *  func - function handler
	 *
	 * See Also:
	 *
	 *  <setResultHandler>, <renderFinalResults>
	 *
	 */ 
	this.getDefaultResultHandler = function() {
		return renderFinalResults;
	}

	/*
	 * Function: defaultSelectAllHandler
	 * Default handler provided for 'select All' operation
	 *
	 * See Also:
	 *
	 *  <setSelectAllHandler>, <selectAll>
	 *
	 */ 
	function defaultSelectAllHandler() {
		toggleSelectAll(true);
	}

	/*
	 * Function: setSelectAllHandler
	 * Can be used to set an alternate handler for 'select All' operations
	 *
	 * See Also:
	 *
	 *  <setSelectAllHandler>, <selectAll>
	 *
	 */ 
	this.setSelectAllHandler = function(func) {
		selectAllHandler = func ? func : defaultSelectAllHandler;
	}


	// Group: Rendering Functions
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Function: render
	 * Initial rendering step
	 *
	 * This is the main entry point of this pseudo-class
	 *
	 */ 
	function render() {
		// Container for new image selection
		var	topDiv = document.createElement('div');
		topDiv.setAttribute('id', id + '_new_image_selection_div');
		container.appendChild(topDiv);
		renderCreateNewImageSelection(topDiv);
	}

	/*
	 * Function: renderFinalResults
	 * Displays grid widget with list of images
	 *
	 * Parameters:
	 *
	 *  idList - array of array of comma-separated list of images' DB ids
	 *  output - DOM node: grid container
	 *  handler - function: custom code to execute once results are loaded into the grid
	 *
	 * See Also:
	 *
	 * <showResultCount>, <setResultHandler>
	 *
	 */ 
	function renderFinalResults(idList, output, handler) {
		removeAllChildrenNodes(output);

		/*
		 * idList may be too long. This is a workaround to prevent "URI too long" issues.
		 *
		 */
		var xhr = new HttpRequest(
			null,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				_tableWidget.setRowIdsFromColumn(0);
				_tableWidget.loadDataFromQuery(	'/youpi/process/query/imgsFromIdList/', 	// path
												'Ids=' + resp['mapList'],					// POST data
												function() {								// Custom handler
													if (handler && typeof handler == 'function')
														handler();
												}
											);

			}
		);

		// Send HTTP POST request
		var post = 'IdList=' + idList;
		xhr.send('/youpi/process/query/remapIds/', post);
	}

	/*
	 * Function: getTableWidget
	 * Returns table widget instance used for rendering results
	 *
	 * Returns:
	 *  object - AdvancedTable instance
	 *
	 */ 
	this.getTableWidget = function() {
		return _tableWidget;
	}

	/*
	 * Function: setTableWidget
	 * Sets table widget instance used for rendering results
	 *
	 * Parameters:
	 *  widget - <AdvancedTable> instance 
	 *
	 */ 
	this.setTableWidget = function(widget) {
		_tableWidget = widget;
		widget.setContainer('_result_grid_div');
	}

	/*
	 * Function: renderSingleSelection
	 * Renders single selection widget
	 *
	 * Parameters:
	 *
	 *   cNode - DOM node parent container
	 *   nbRes - integer: number of ingested images into DB
	 *
	 */ 
	function renderSingleSelection(cNode, nbRes) {
		// div for single selection
		var single_div = document.createElement('div');
		single_div.setAttribute('id', id + '_single_sel_div');

		var div = document.createElement('div');
		div.setAttribute('class', 'headerText');
		div.appendChild(document.createTextNode(caption));
		var snb = document.createElement('span');
		snb.setAttribute('style', 'font-weight: bold;');
		snb.appendChild(document.createTextNode(nbRes));
		div.appendChild(snb);
		div.appendChild(document.createTextNode(' images those for which:'));
		single_div.appendChild(div);

		// Table
		topNode = document.createElement('table');
		var tab = topNode;
		var tr = document.createElement('tr');
		tab.appendChild(tr);
		single_div.appendChild(tab);
		cNode.appendChild(single_div);

		// Second row
		addTRLine(tr);

		// Execute query
		div = document.createElement('div');
		div.setAttribute('style', 'text-align: left');
		var sub = document.createElement('input');
		sub.setAttribute('type', 'button');
		sub.setAttribute('value', 'Find images!');
		sub.setAttribute('onclick', _instance_name + '.executeQuery();');
		div.appendChild(sub);
		single_div.appendChild(div);

		// Div that display results count
		div = document.createElement('div');
		div.setAttribute('id', id + '_result_count_div');
		single_div.appendChild(div);

		// Result grid
		div = document.createElement('div');
		div.setAttribute('id', '_result_grid_div');
		div.setAttribute('style', 'width: ' + div.width + 'px; height: 90%;');
		single_div.appendChild(div);

		// Result div
		div = document.createElement('div');
		div.setAttribute('id', id + '_result_div');
		div.setAttribute('style', 'height: 100%; width: 100%; overflow: hidden;');
		single_div.appendChild(div);
	}

	/*
	 * Function: renderBatchSelection
	 * Renders batch selection widget
	 *
	 * Parameters:
	 *
	 *   cNode - DOM node parent container
	 *   nbRes - integer: number of ingested images into DB
	 *
	 */ 
	function renderBatchSelection(cNode, nbRes) {
		// div for batch selection
		var batch_div = document.createElement('div');
		batch_div.setAttribute('id', id + '_batch_sel_div');

		var form = document.createElement('form');
		form.setAttribute('action', '/youpi/uploadFile/');
		form.setAttribute('enctype', 'multipart/form-data');
		form.setAttribute('method', 'post');
		form.setAttribute('onsubmit', "return " + _instance_name + ".getAIM().submit(this, {'onStart' : " + _instance_name + ".getFileUploadStartHandler(), 'onComplete' : " + _instance_name + ".getFileUploadCompleteHandler()});");

		var xl = document.createElement('label');
		xl.appendChild(document.createTextNode('Select an XML file to upload: '));

		var filei = document.createElement('input');
		filei.setAttribute('type', 'file');
		filei.setAttribute('name', 'xmlfile');
		xl.appendChild(filei);

		var subi = document.createElement('input');
		subi.setAttribute('style', 'margin-left: 10px;');
		subi.setAttribute('type', 'submit');
		subi.setAttribute('value', 'Upload and check file');

		form.appendChild(xl);
		form.appendChild(subi);

		batch_div.appendChild(form);

		// for saved selections
		var sdiv = document.createElement('div');
		sdiv.setAttribute('id', id + '_batch_load_saved_sel_div');
		batch_div.appendChild(sdiv);

		var r = document.createElement('div');
		r.setAttribute('style', 'color: green; background-color: white; float: left; margin-right: 30px;');
		r.setAttribute('id', id + '_upload_log_div');
		batch_div.appendChild(r);

		r = document.createElement('div');
		r.setAttribute('id', id + '_sky_selections_div');
		r.setAttribute('title', 'Click on image to see larger version');
		batch_div.appendChild(r);

		cNode.appendChild(batch_div);
	}

	/*
	 * Function: _getOptionsToolbar
	 * Build a toolbar widget with action buttons depending on selection mode
	 *
	 * Returns:
	 *  DOM node
	 *
	 */ 
	function _getOptionsToolbar() {
		var div = document.createElement('div');
		div.setAttribute('class', 'modeOptions');

		switch(_selectionMode) {
			case _singleMode:
				// Merge saved selections
				var d = document.createElement('div');
				d.setAttribute('id', id + '_merge_selections_div');
				d.setAttribute('style', 'padding: 5px;');
				var sub = document.createElement('input');
				sub.setAttribute('type', 'button');
				sub.setAttribute('value', 'Merge with existing selections...');
				sub.setAttribute('onclick', _instance_name + '.showMergeSelectionsBox();');
				d.appendChild(sub);
				div.appendChild(d);

				// Select all
				sub = document.createElement('input');
				sub.setAttribute('style', 'margin-right: 10px;');
				sub.setAttribute('type', 'button');
				sub.setAttribute('value', 'Select all');
				sub.setAttribute('onclick', _instance_name + '.selectAll();');
				div.appendChild(sub);

				// Unselect all
				sub = document.createElement('input');
				sub.setAttribute('type', 'button');
				sub.setAttribute('value', 'Unselect all');
				sub.setAttribute('onclick', _instance_name + '.unselectAll();');
				div.appendChild(sub);
				break;

			case _batchMode:
				div.appendChild(_createCheckBox(_instance_name + '_batch_display_sky_check', true, 'Display sky visualization'));
				div.appendChild(_createCheckBox(_instance_name + '_batch_sky_compute_all_check', false, 'Plot all images points, not only selections (slower)'));
				div.setAttribute('style', 'text-align: left;');
				break;

			default:
				break;
		}

		return div;
	}

	/*
	 * Function: _createCheckBox
	 * Build a checkbox DOM object 
	 *
	 * Parameters:
	 *  id - string: unique id of checkbox
	 *  checked - boolean: default state
	 *  label - string: Checkbox's label
	 *
	 * Returns:
	 *  DOM div container of checkbox
	 *
	 */ 
	function _createCheckBox(id, checked, label) {
		var s = document.createElement('div');
		s.setAttribute('style', 'color: white; margin-left: 10px; margin-right: 5px;');
		var input = document.createElement('input');
		input.setAttribute('id', id);
		input.setAttribute('type', 'checkbox');
		if (checked)
			input.setAttribute('checked', 'checked');

		var lab = document.createElement('label');
		lab.appendChild(document.createTextNode('   ' + label));

		s.appendChild(input);
		s.appendChild(lab);

		return s;
	}

	/*
	 * Function: _getContextTip
	 * Displays a contextual tip depending on selection mode
	 *
	 * Returns:
	 *  DOM node
	 *
	 */ 
	function _getContextTip() {
		var div = document.createElement('div');
		div.setAttribute('class', 'tip');
		div.setAttribute('style', 'width: 73%;');
		var msg;

		switch(_selectionMode) {
			case _singleMode:
				msg = "Select criterias on the right and click the &laquo;<b>Find images!</b>&raquo; button to build an image selection.";
				break;

			case _batchMode:
				msg = "Upload an XML file to build a list of images selections.";
				break;

			default:
				break;
		}

		div.innerHTML = msg;

		return div;
	}

	/*
	 * Function: _getEditSelectionBox
	 * Build edit selection widget
	 *
	 * Returns:
	 *   DOM node of widget
	 *
	 */ 
	function _getEditSelectionBox() {
		// Selection related
		var bdiv = document.createElement('div');
		bdiv.setAttribute('id', id + '_selection_box_div');
		bdiv.setAttribute('class', 'controlPanel');

		// Save selection
		div = document.createElement('div');
		div.setAttribute('id', id + '_save_selection_div');
		sub = document.createElement('input');
		sub.setAttribute('type', 'button');
		sub.setAttribute('value', 'Save selection as...');
		sub.setAttribute('onclick', _instance_name + '.showSaveSelectionBox();');
		div.appendChild(sub);
		bdiv.appendChild(div);

		// Delete existing selection
		div = document.createElement('div');
		div.setAttribute('id', id + '_delete_selection_div');
		sub = document.createElement('input');
		sub.setAttribute('type', 'button');
		sub.setAttribute('value', 'Delete existing selection...');
		sub.setAttribute('onclick', _instance_name + '.showDeleteSelectionBox();');
		div.appendChild(sub);
		bdiv.appendChild(div);

		return bdiv;
	}

	/*
	 * Function: renderCreateNewImageSelection
	 * Queries number of images ingested into DB and initiates widget rendering
	 *
	 * Parameters:
	 *
	 *   containerNode - DOM node parent container
	 *
	 */ 
	function renderCreateNewImageSelection(containerNode) {
		var xhr = new HttpRequest(
			containerNode.id,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				var nb = resp['Total'];

				// x3 (firebug issue)
				removeAllChildrenNodes(containerNode);
				removeAllChildrenNodes(containerNode);
				removeAllChildrenNodes(containerNode);

				addImageQueryForm(containerNode, nb);

			}
		);

		// Send HTTP POST request
		xhr.send('/youpi/ingestion/imgCount/');
	}

	/*
	 * Function: showDeleteSelectionBox
	 * _Public_ Display selection box used for deleting DB image selections
	 *
	 */ 
	this.showDeleteSelectionBox = function() {
		var div = document.getElementById(id + '_delete_selection_div');
		var sub = document.getElementById(id + '_delete_selection_subdiv');

		if (!sub) {
			sub = document.createElement('div');
			sub.setAttribute('id', id + '_delete_selection_subdiv');
			sub.setAttribute('class', 'show');
			div.appendChild(sub);
		}
		else {
			if (sub.getAttribute('class') == 'show') {
				sub.setAttribute('class', 'hide');
				return;
			}
			else {
				sub.setAttribute('class', 'show');
			}
		}

		// Retrieves all image selections stored into DB
		getImageSelections(sub, function(resp) {
			removeAllChildrenNodes(sub);
			removeAllChildrenNodes(sub);

			if (resp['data'].length == 0) {
				var p = document.createElement('p');
				p.setAttribute('class', 'error');
				p.appendChild(document.createTextNode('No saved selections found.'));
				p.appendChild(document.createElement('br'));
				p.appendChild(document.createTextNode('Nothing to delete.'));
				sub.appendChild(p);
				return;
			}

			var options = [];
			for (var k=0; k < resp['data'].length; k++) {
				options[k] = resp['data'][k][0];
			}
			var sel = getSelect(id + '_del_selection_combo', options);
			sub.appendChild(sel);

			var del = document.createElement('input');
			del.setAttribute('type', 'button');
			del.setAttribute('onclick', _instance_name + '.deleteSavedSelection();');
			del.setAttribute('value', 'Delete!');
			sub.appendChild(del);
		});
	}

	/*
	 * Function: showMergeSelectionBox
	 * _Public_ Display selection box used for merging DB image selections
	 *
	 */ 
	this.showMergeSelectionsBox = function() {
		if (!_getListsOfSelections()) {
			alert(imgSelRequiredMsg);
			return;
		}
		var div = document.getElementById(id + '_merge_selections_div');
		var sub = document.getElementById(id + '_merge_selections_subdiv');
		
		if (!sub) {
			sub = document.createElement('div');
			sub.setAttribute('id', id + '_merge_selections_subdiv');
			sub.setAttribute('class', 'show');
			div.appendChild(sub);
		}
		else {
			if (sub.getAttribute('class') == 'show') {
				sub.setAttribute('class', 'hide');
				return;
			}
			else {
				sub.setAttribute('class', 'show');
			}
		}

		// Retrieves all image selections stored into DB
		getImageSelections(sub, function(resp) {
			removeAllChildrenNodes(sub);
			removeAllChildrenNodes(sub);
			var len = resp['data'].length;

			if (len == 0) {
				var p = document.createElement('p');
				p.setAttribute('class', 'error');
				p.appendChild(document.createTextNode('No saved selections found.'));
				p.appendChild(document.createElement('br'));
				p.appendChild(document.createTextNode('Nothing to merge.'));
				sub.appendChild(p);
				return;
			}

			var p = document.createElement('p');
			p.setAttribute('style', 'font-style: italic');
			p.appendChild(document.createTextNode(len + ' ' + (len > 1 ? 'selections' : 'selection') + ' available'));
			sub.appendChild(p);

			var options = []
			for (var k=0; k < len; k++) {
				options[k] = resp['data'][k][0];
			}
			var combosize = options.length > 5 ? 8 : options.length
			var sel = getSelect(id + '_merge_selections_combo', options, combosize);
			sub.appendChild(sel);

			var del = document.createElement('input');
			del.setAttribute('type', 'button');
			del.setAttribute('onclick', _instance_name + '.mergeSavedSelections();');
			del.setAttribute('value', 'Merge!');
			sub.appendChild(del);
		});
	}

	/*
	 * Function: showSaveSelectionBox
	 * _Public_ Display selection box used for saving DB image selections
	 *
	 */ 
	this.showSaveSelectionBox = function() {
		if (!_getListsOfSelections()) {
			alert(imgSelRequiredMsg);
			return;
		}

		var div = document.getElementById(id + '_save_selection_div');
		var sub = document.getElementById(id + '_save_selection_subdiv');

		if (!sub) {
			sub = document.createElement('div');
			sub.setAttribute('id', id + '_save_selection_subdiv');
			sub.setAttribute('class', 'show');

			var txt = document.createElement('input');
			txt.setAttribute('style', 'float: left; margin-right: 5px;');
			txt.setAttribute('id', id + '_save_selection_text');
			txt.setAttribute('type', 'text');
			sub.appendChild(txt);

			var save = document.createElement('input');
			save.setAttribute('type', 'button');
			save.setAttribute('onclick', _instance_name + '.saveSelection();');
			save.setAttribute('value', 'Save!');
			sub.appendChild(save);

			var res = document.createElement('div');
			res.setAttribute('id', id + '_save_selection_res_div');
			res.setAttribute('style', 'vertical-align: middle');
			sub.appendChild(res);

			div.appendChild(sub);

			// Add auto-completion capabilities
			if (_bsn) {
				var options = {
					script: '/youpi/autocompletion/ImageSelections/',
					varname: 'Value',
					json: true,
					maxresults: 20,
					timeout: 3000
				};
				var au = new _bsn.AutoSuggest(id + '_save_selection_text', options);
			}

			txt.focus();
		}
		else {
			if (sub.getAttribute('class') == 'show') {
				sub.setAttribute('class', 'hide');
			}
			else {
				sub.setAttribute('class', 'show');
				var nText = document.getElementById(id + '_save_selection_text');
				nText.select();
				nText.focus();
			}
		}
	}


	// Group: Search Critera Related Functions
	// -----------------------------------------------------------------------------------------------------------------------------


	// Group: Object Field
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Function: buildObjectDataWidget
	 * Dynamically builds DOM content for the 'Object' search criteria
	 *
	 * Parameters:
	 *
	 *  tr_idx - string: id of DOM container element
	 *
	 */ 
	function buildObjectDataWidget(tr_idx) {
		var output = document.getElementById(id + '_custom_div_' + tr_idx);

		var xhr = new HttpRequest(
			output.id,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				// Rendering
				removeAllChildrenNodes(output);
				var selNode = getSelect(id + '_object_select_' + tr_idx, resp['data'], 6);
				output.appendChild(selNode);
			}
		);

		// Build custom query
		var data = 'Distinct=&Table=youpi_image&DisplayField=object&Lines=0&Line0Field=object&Line0Cond=contains&Line0Text=&Hide=&OrderBy=object';
		// Send POST HTTP query
		xhr.send('/youpi/process/preingestion/query/', data);
	}

	/*
	 * Function: getObjectCondSelect
	 * Returns DOM select object for the 'Object' search criteria
	 *
	 * Parameters:
	 *
	 *  tr_idx - string: id of DOM container element
	 *
	 * Returns:
	 *
	 *  DOM select element
	 *
	 */ 
	function getObjectCondSelect(tr_idx) {
		var conds = ['is equal to', 'is different from'];
		return getSelect(id + '_condition_select_' + tr_idx, conds);
	}

	/*
	 * Function: getObjectSQLParams
	 * Returns a JSON object with custom SQL parameters for the 'Object' search criteria
	 *
	 * These parameters will be used by <sendq> when sending POST request to the server.
	 *
	 * Returns:
	 *
	 *  JSON element
	 *
	 */ 
	function getObjectSQLParams() {
		// ftable: foreign SQL table
		return {'ftable' 	: null,
				'field': 'object'};
	}


	// Group: Ingestion Field
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Function: buildIngestionIdDataWidget
	 * Dynamically builds DOM content for the 'IngestionId' search criteria
	 *
	 * Parameters:
	 *
	 *  tr_idx - string: id of DOM container element
	 *
	 */ 
	function buildIngestionIdDataWidget(tr_idx) {
		var output = document.getElementById(id + '_custom_div_' + tr_idx);

		var xhr = new HttpRequest(
			output.id,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				// Rendering
				removeAllChildrenNodes(output);
				var selNode = getSelect(id + '_ingestionId_select_' + tr_idx, resp['data']);
				output.appendChild(selNode);
			}
		);

		// Build custom query
		var data = 'Distinct=&Table=youpi_ingestion&DisplayField=label&Lines=0&Line0Field=label&Line0Cond=contains&Line0Text=&Hide=&OrderBy=label';
		// Send POST HTTP query
		xhr.send('/youpi/process/preingestion/query/', data);
	}

	/*
	 * Function: getIngestionIdCondSelect
	 * Returns DOM select object for the 'IngestionId' search criteria
	 *
	 * Parameters:
	 *
	 *  tr_idx - string: id of DOM container element
	 *
	 * Returns:
	 *
	 *  DOM select element
	 *
	 */ 
	function getIngestionIdCondSelect(tr_idx) {
		var conds = ['is equal to', 'is different from'];
		return getSelect(id + '_condition_select_' + tr_idx, conds);
	}

	/*
	 * Function: getIngestionIdSQLParams
	 * Returns a JSON object with custom SQL parameters for the 'IngestionId' search criteria
	 *
	 * These parameters will be used by <sendq> when sending POST request to the server.
	 *
	 * Returns:
	 *
	 *  JSON element
	 *
	 */ 
	function getIngestionIdSQLParams() {
		// ftable: foreign SQL table
		return {'ftable' 		: 'youpi_ingestion',
				'ftable_field' 	: 'label',
				'fkid'			: 'ingestion_id',
				'ftable_id' 	: 'id' };
	}


	// Group: Channel Field
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Function: buildChannelDataWidget
	 * Dynamically builds DOM content for the 'Channel' search criteria
	 *
	 * Parameters:
	 *
	 *  tr_idx - string: id of DOM container element
	 *
	 */ 
	function buildChannelDataWidget(tr_idx) {
		var output = document.getElementById(id + '_custom_div_' + tr_idx);

		var xhr = new HttpRequest(
			output.id,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				// Rendering
				removeAllChildrenNodes(output);
				var selNode = getSelect(id + '_channel_select_' + tr_idx, resp['data'], 6);
				output.appendChild(selNode);
			}
		);

		// Build custom query
		var data = 'Distinct=&Table=youpi_channel&DisplayField=name&Lines=0&Line0Field=name&Line0Cond=contains&Line0Text=&Hide=&OrderBy=name';
		// Send POST HTTP query
		xhr.send('/youpi/process/preingestion/query/', data);
	}

	/*
	 * Function: getChannelCondSelect
	 * Returns DOM select object for the 'Channel' search criteria
	 *
	 * Parameters:
	 *
	 *  tr_idx - string: id of DOM container element
	 *
	 * Returns:
	 *
	 *  DOM select element
	 *
	 */ 
	function getChannelCondSelect(tr_idx) {
		var conds = ['is equal to', 'is different from'];
		return getSelect(id + '_condition_select_' + tr_idx, conds);
	}

	/*
	 * Function: getChannelSQLParams
	 * Returns a JSON object with custom SQL parameters for the 'Channel' search criteria
	 *
	 * These parameters will be used by <sendq> when sending POST request to the server.
	 *
	 * Returns:
	 *
	 *  JSON element
	 *
	 */ 
	function getChannelSQLParams() {
		return {'ftable' 		: 'youpi_channel',
				'ftable_field' 	: 'name',
				'fkid'			: 'channel_id',
				'ftable_id' 	: 'id' };
	}


	// Group: Instrument Field
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Function: buildInstrumentDataWidget
	 * Dynamically builds DOM content for the 'Instrument' search criteria
	 *
	 * Parameters:
	 *
	 *  tr_idx - string: id of DOM container element
	 *
	 */ 
	function buildInstrumentDataWidget(tr_idx) {
		var output = document.getElementById(id + '_custom_div_' + tr_idx);

		var xhr = new HttpRequest(
			output.id,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				// Rendering
				removeAllChildrenNodes(output);
				var selNode = getSelect(id + '_instrument_select_' + tr_idx, resp['data']);
				output.appendChild(selNode);
			}
		);

		// Build custom query
		var data = 'Distinct=&Table=youpi_instrument&DisplayField=name&Lines=0&Line0Field=name&Line0Cond=contains&Line0Text=&Hide=&OrderBy=name';

		// Send POST HTTP query
		xhr.send('/youpi/process/preingestion/query/', data);
	}

	/*
	 * Function: getInstrumentCondSelect
	 * Returns DOM select object for the 'Instrument' search criteria
	 *
	 * Parameters:
	 *
	 *  tr_idx - string: id of DOM container element
	 *
	 * Returns:
	 *
	 *  DOM select element
	 *
	 */ 
	function getInstrumentCondSelect(tr_idx) {
		var conds = ['is equal to', 'is different from'];
		return getSelect(id + '_condition_select_' + tr_idx, conds);
	}

	/*
	 * Function: getInstrumentSQLParams
	 * Returns a JSON object with custom SQL parameters for the 'Instrument' search criteria
	 *
	 * These parameters will be used by <sendq> when sending POST request to the server.
	 *
	 * Returns:
	 *
	 *  JSON element
	 *
	 */ 
	function getInstrumentSQLParams() {
		return {'ftable' 		: 'youpi_instrument',
				'ftable_field' 	: 'name',
				'fkid'			: 'instrument_id',
				'ftable_id' 	: 'id' };
	}


	// Group: Run Field
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Function: buildRunDataWidget
	 * Dynamically builds DOM content for the 'Run' search criteria
	 *
	 * Parameters:
	 *
	 *  tr_idx - string: id of DOM container element
	 *
	 */ 
	function buildRunDataWidget(tr_idx) {
		var output = document.getElementById(id + '_custom_div_' + tr_idx);

		var xhr = new HttpRequest(
			output.id,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				// Rendering
				removeAllChildrenNodes(output);
				var selNode = getSelect(id + '_run_select_' + tr_idx, resp['data'], 6);
				output.appendChild(selNode);
			}
		);

		// Build custom query
		var data = 'Distinct=&Table=youpi_run&DisplayField=name&Lines=0&Line0Field=name&Line0Cond=contains&Line0Text=&Hide=&OrderBy=name';

		// Send POST HTTP query
		xhr.send('/youpi/process/preingestion/query/', data);
	}

	/*
	 * Function: getRunCondSelect
	 * Returns DOM select object for the 'Run' search criteria
	 *
	 * Parameters:
	 *
	 *  tr_idx - string: id of DOM container element
	 *
	 * Returns:
	 *
	 *  DOM select element
	 *
	 */ 
	function getRunCondSelect(tr_idx) {
		var conds = ['is equal to', 'is different from'];
		return getSelect(id + '_condition_select_' + tr_idx, conds);
	}

	/*
	 * Function: getRunSQLParams
	 * Returns a JSON object with custom SQL parameters for the 'Run' search criteria
	 *
	 * These parameters will be used by <sendq> when sending POST request to the server.
	 *
	 * Returns:
	 *
	 *  JSON element
	 *
	 */ 
	function getRunSQLParams() {
		return {'ftable' 		: 'youpi_run',
				'ftable_field' 	: 'name',
				'fkid'			: 'run_id',
				'ftable_id' 	: 'id' };
	}


	// Group: Saved Selection Field
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Function: buildSavedDataWidget
	 * Dynamically builds DOM content for the 'Saved' search criteria
	 *
	 * Parameters:
	 *
	 *  tr_idx - string: id of DOM container element
	 *
	 */ 
	function buildSavedDataWidget(tr_idx) {
		var output = document.getElementById(id + '_custom_div_' + tr_idx);

		var xhr = new HttpRequest(
			output.id,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				// Rendering
				removeAllChildrenNodes(output);
				var selid = id + '_saved_select_' + tr_idx;
				if (resp['data'].length > 0) {
					var sels = new Array();
					for (var k=0; k < resp['data'].length; k++) {
						sels[k] = resp['data'][k][0];
					}
					var selNode = getSelect(selid, sels);
				}
				else {
					var selNode = document.createElement('select');
					selNode.setAttribute('id', selid);
					option = document.createElement('option');
					option.setAttribute('value', 0);
					option.appendChild(document.createTextNode('-- No saved selection in database --'));
					selNode.appendChild(option);
				}
				output.appendChild(selNode);
			}
		);

		var post = 'Mode=Single';
		xhr.send('/youpi/process/db/getSelections/', post);
	}

	/*
	 * Function: getSavedCondSelect
	 * Returns DOM select object for the 'Saved' search criteria
	 *
	 * Parameters:
	 *
	 *  tr_idx - string: id of DOM container element
	 *
	 * Returns:
	 *
	 *  DOM select element
	 *
	 */ 
	function getSavedCondSelect(tr_idx) {
		var conds = ['is equal to'];
		return getSelect(id + '_condition_select_' + tr_idx, conds);
	}

	/*
	 * Function: getSavedSQLParams
	 * Returns a JSON object with custom SQL parameters for the 'Saved' search criteria
	 *
	 * These parameters will be used by <sendq> when sending POST request to the server.
	 *
	 * Returns:
	 *
	 *  JSON element
	 *
	 */ 
	function getSavedSQLParams() {
		/*
		 * Only this special string to instruct send_q() to make a non-standard (different url) call
		 *
		 */
		return {'special' : true};
	}


	// Group: Name Field
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Function: buildNameDataWidget
	 * Dynamically builds DOM content for the 'Name' search criteria
	 *
	 * Parameters:
	 *
	 *  tr_idx - string: id of DOM container element
	 *
	 */ 
	function buildNameDataWidget(tr_idx) {
		var output = document.getElementById(id + '_custom_div_' + tr_idx);
		var txtNode = document.createElement('input');
		txtNode.setAttribute('type', 'text');

		removeAllChildrenNodes(output);
		output.appendChild(txtNode);
	}

	/*
	 * Function: getNameCondSelect
	 * Returns DOM select object for the 'Name' search criteria
	 *
	 * Parameters:
	 *
	 *  tr_idx - string: id of DOM container element
	 *
	 * Returns:
	 *
	 *  DOM select element
	 *
	 */ 
	function getNameCondSelect(tr_idx) {
		var conds = ['matches'];
		return getSelect(id + '_condition_select_' + tr_idx, conds);
	}

	/*
	 * Function: getNameSQLParams
	 * Returns a JSON object with custom SQL parameters for the 'Name' search criteria
	 *
	 * These parameters will be used by <sendq> when sending POST request to the server.
	 *
	 * Returns:
	 *
	 *  JSON element
	 *
	 */ 
	function getNameSQLParams() {
		return {'ftable' 	: null,
				'field'		: 'name'};
	}


	// Group: Ra Field
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Function: buildRaDataWidget
	 * Dynamically builds DOM content for the 'Ra' search criteria
	 *
	 * Parameters:
	 *
	 *  tr_idx - string: id of DOM container element
	 *
	 */ 
	function buildRaDataWidget(tr_idx) {
		var output = document.getElementById(id + '_custom_div_' + tr_idx);
		var txtNode = document.createElement('input');
		txtNode.setAttribute('type', 'text');

		removeAllChildrenNodes(output);
		output.appendChild(txtNode);
	}

	/*
	 * Function: getRaCondSelect
	 * Returns DOM select object for the 'Ra' search criteria
	 *
	 * Parameters:
	 *
	 *  tr_idx - string: id of DOM container element
	 *
	 * Returns:
	 *
	 *  DOM select element
	 *
	 */ 
	function getRaCondSelect(tr_idx) {
		var conds = ['is equal to', 'is greater than', 'is lower than'];
		return getSelect(id + '_condition_select_' + tr_idx, conds);
	}

	/*
	 * Function: getRaSQLParams
	 * Returns a JSON object with custom SQL parameters for the 'Ra' search criteria
	 *
	 * These parameters will be used by <sendq> when sending POST request to the server.
	 *
	 * Returns:
	 *
	 *  JSON element
	 *
	 */ 
	function getRaSQLParams() {
		return {'ftable' 	: null,
				'field': 'alpha'};
	}


	// Group: Dec Field
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Function: buildDecDataWidget
	 * Dynamically builds DOM content for the 'Dec' search criteria
	 *
	 * Parameters:
	 *
	 *  tr_idx - string: id of DOM container element
	 *
	 */ 
	function buildDecDataWidget(tr_idx) {
		var output = document.getElementById(id + '_custom_div_' + tr_idx);
		var txtNode = document.createElement('input');
		txtNode.setAttribute('type', 'text');

		removeAllChildrenNodes(output);
		output.appendChild(txtNode);
	}

	/*
	 * Function: getDecCondSelect
	 * Returns DOM select object for the 'Dec' search criteria
	 *
	 * Parameters:
	 *
	 *  tr_idx - string: id of DOM container element
	 *
	 * Returns:
	 *
	 *  DOM select element
	 *
	 */ 
	function getDecCondSelect(tr_idx) {
		var conds = ['is equal to', 'is greater than', 'is lower than'];
		return getSelect(id + '_condition_select_' + tr_idx, conds);
	}

	/*
	 * Function: getDecSQLParams
	 * Returns a JSON object with custom SQL parameters for the 'Dec' search criteria
	 *
	 * These parameters will be used by <sendq> when sending POST request to the server.
	 *
	 * Returns:
	 *
	 *  JSON element
	 *
	 */ 
	function getDecSQLParams() {
		return {'ftable' 	: null,
				'field': 'delta'};
	}


	// Group: Misc. Functions
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Function: _getListsOfSelections 
	 * Returns selection(s) of images, if any.
	 *
	 * Returns:
	 *  array of selections, null if no selection
	 *
	 */ 
	function _getListsOfSelections() {
		switch(_selectionMode) {
			case _singleMode:
				var sel = _tableWidget.getSelectedRows();
				var nb = 0;

				if (sel.length > 0)
					nb = sel.split(',').length;
				if (!nb) return null;

				_singleModeSelections = '[[' + sel + ']]';
				_imagesCount = nb;

				return _singleModeSelections;
				break;

			case _batchMode:
				if (_batchModeSelections.length) {
					_imagesCount = 0;
					var msels = '[';
					for (var k=0; k < _batchModeSelections.length; k++) {
						msels += '[' + _batchModeSelections[k] + ']';
						_imagesCount += _batchModeSelections[k].split(',').length;
						if (k < _batchModeSelections.length-1) msels += ',';
					}
					msels += ']';
					return msels;
				}
				else
					return null;
				break;

			default:
				break;
		}
	}

	/*
	 * Function: getListsOfSelections 
	 * Returns selection(s) of images, if any.
	 *
	 * Note:
	 *  This is a public wrapper of <_getListsOfSelections>
	 *
	 */ 
	this.getListsOfSelections = function() {
		return _getListsOfSelections();
	}

	/*
	 * Function: getImagesCount 
	 * Returns total of images in all selections
	 *
	 * Returns:
	 *  integer - total of images selected
	 *
	 */ 
	 this.getImagesCount = function() { return _imagesCount; }

	/*
	 * Function: genID 
	 * Try to generate a pseudo unique string ID
	 *
 	 * Parameters:
	 *	name - string: name part of ID 
	 *  row - integer: for row number
	 *
	 * Returns:
	 *  pseudo unique string id
	 *
	 */ 
	function genID(name, row) {
		var row = row || currentTR;
		return id + name + row;
	}

	/*
	 * Function: getTopNode 
	 * Returns top DOM table element
	 *
 	 * Parameters:
	 *	name - string: name part of ID 
	 *  row - integer: row number
	 *
	 * Returns:
	 *  DOM table element 
	 *
	 */ 
	this.getTopNode = function() { return topNode; }

	/*
	 * Function: removeAllChildrenNodes 
	 * Deletes a DOM node's children
	 *
 	 * Parameters:
	 *	node - DOM parent node
	 *
	 */ 
	function removeAllChildrenNodes(node)
	{
		// Element ?
		if (node.nodeType != 1)
			return;
	
		if (node.hasChildNodes()) {
			for (var n=0; n < node.childNodes.length; n++) {
				if(!node.removeChild(node.childNodes[n]))
					alert('Could not remove ' + node);
			}
		}
	}

	/*
	 * Function: _swapSelectionMode 
	 * This function swaps display between selection modes.
	 *
	 * The ImageSelector widget has 2 selection modes:
	 *
	 *  Single selection mode - only one selection of images can be built
	 *  Batch selection mode - many selections of images can be built at a time
	 *
	 */ 
	function _swapSelectionMode() {
		var msel = document.getElementById(id + '_image_mode_sel');
		/* 
		 * mode = 0 - SM
		 * mode = 1 - BM
		 */
		var mode = msel.selectedIndex;
		var sdiv = document.getElementById(id + '_single_sel_div');
		var bdiv = document.getElementById(id + '_batch_sel_div');

		_selectionMode = mode;

		if (mode) {
			// Batch
			sdiv.style.display = 'none';
			bdiv.style.display = 'block';

			_updateBatchSavedSelectionArea();
		}
		else {
			// Single
			sdiv.style.display = 'block';
			bdiv.style.display = 'none';
		}

		var optdiv = document.getElementById(id + '_mode_options_div');
		optdiv.innerHTML = '';
		optdiv.appendChild(_getOptionsToolbar());

		var tipdiv = document.getElementById(id + '_mode_options_tip_div');
		tipdiv.innerHTML = '';
		tipdiv.appendChild(_getContextTip());
	}

	/*
	 * Function: _updateBatchSavedSelectionArea 
	 * Checks if batch saved selections are available
	 *
	 */ 
	function _updateBatchSavedSelectionArea() {
		var	seldiv = document.getElementById(id + '_batch_load_saved_sel_div');
	
		var xhr = new HttpRequest(
			seldiv,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				var data = resp['data'];
				seldiv.innerHTML = '';

				if (!data.length) return;
	
				var r = new Array();
				for (var k=0; k < data.length; k++) {
					r[k] = data[k][0];
				}
	
				seldiv.appendChild(document.createTextNode('Or load a saved selection: '));
				seldiv.appendChild(getSelect(id + '_batch_load_saved_sel', r));
	
				var lbut = document.createElement('input');
				lbut.setAttribute('style', 'margin-left: 10px;');
				lbut.setAttribute('type', 'button');
				lbut.setAttribute('onclick', _instance_name + ".loadBatchSavedSelection();");
				lbut.setAttribute('value', 'Load');
		
				seldiv.appendChild(lbut);

				var blog = document.createElement('div');
				blog.setAttribute('id', id + '_batch_load_saved_log_div');
				blog.setAttribute('style', 'float: left;');
				seldiv.appendChild(blog);
			}
		);
	
		var post = 'Mode=Batch';
		xhr.send('/youpi/process/db/getSelections/', post);
	}

	/*
	 * Function: loadBatchSavedSelection 
	 * Loads a batch saved selection
	 *
	 */ 
	this.loadBatchSavedSelection = function() {
		var	div = document.getElementById(id + '_batch_load_saved_log_div');
		var sel = document.getElementById(id + '_batch_load_saved_sel');
		var name = sel.options[sel.selectedIndex].text;
		document.getElementById(id + '_upload_log_div').innerHTML = '';
		document.getElementById(id + '_sky_selections_div').innerHTML = '';

		var xhr = new HttpRequest(
			div,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				div.innerHTML = '';
				sels = eval(resp['data']);

				var log = new Logger(div);
				log.msg_ok("Selection '" + name + "' is a list of " + sels.length + ' selection' + (sels.length > 1 ? 's' : ''));

				var count, total = 0;
				// Reset batch selections
				_batchModeSelections.length = 0;

				for (var k=0; k < sels.length; k++) {
					count = sels[k].length;
					log.msg_status('Selection ' + (k+1) + ' contains ' + count + ' images');
					// link.setAttribute('onclick', _instance_name + ".viewBatchSelection('" + encodeURI(sel[k]['xml']) + "');");
					// Casts array to string with commas
					_batchModeSelections[k] = '' + sels[k] + '';
					total += count;
				}
				log.msg_ok(total + ' images have been selected');

				// Load sky map
				_displaySkyVisualization();
			}
		);

		post = 'Name=' + name + '&Mode=Batch';
		xhr.setBusyMsg("Loading content for list '" + name + "'");
		xhr.send('/youpi/process/db/getSelections/', post);
	}

	/*
	 * Function: swapSelectionMode 
	 * _Public_ This function swaps display between selection modes.
	 *
	 * See Also:
	 *  <_swapSelectionMode>
	 *
	 */ 
	this.swapSelectionMode = function() {
		_swapSelectionMode();
	}

	/*
	 * Function: addImageQueryForm
	 * Displays image query form with a combobox to choose mode selection 
	 *
	 * Parameters:
	 *
	 *   cNode - DOM node parent container
	 *   nbRes - integer: number of ingested images into DB
	 *
	 */ 
	function addImageQueryForm(cNode, nbRes) {
		var sdiv = document.createElement('div');
		sdiv.setAttribute('class', 'image_mode');
		var modes = ['Single selection', 'Batch selection'];
		var lab = document.createElement('label');
		lab.appendChild(document.createTextNode('Selection mode: '));

		var msel = getSelect(id + '_mode_sel', modes);
		msel.setAttribute('id', id + '_image_mode_sel');
		msel.setAttribute('onchange', _instance_name + '.swapSelectionMode()');

		sdiv.appendChild(lab);
		lab.appendChild(msel);
		cNode.appendChild(sdiv);

		var bltab = document.createElement('table');
		bltab.setAttribute('class', 'optionsPanel');
		cNode.appendChild(bltab);

		var tr = document.createElement('tr');
		bltab.appendChild(tr);

		var td = document.createElement('td');
		var ediv = document.createElement('div');
		ediv.appendChild(_getEditSelectionBox());
		td.appendChild(ediv);

		var optdiv = document.createElement('div');
		optdiv.setAttribute('id', id + '_mode_options_div');
		td.appendChild(optdiv);

		var tipdiv = document.createElement('div');
		tipdiv.setAttribute('id', id + '_mode_options_tip_div');
		td.appendChild(tipdiv);

		tr.appendChild(td);

		td = document.createElement('td');
		td.setAttribute('style', 'width: 100%;');
		tr.appendChild(td);

		renderSingleSelection(td, nbRes);
		renderBatchSelection(td, nbRes);

		// Default mode: single selection
		_swapSelectionMode();
	}

	/*
	 * Function: getImageSelections
	 * Get image selections
	 *
	 * Parameters:
	 *
	 *   cNode - DOM node parent container
	 *   resHandler - function: result function handler
	 *
	 */ 
	function getImageSelections(cnode, resHandler) {
		var xhr = new HttpRequest(
			cnode.id,
			// Use default error handler
			null,
			// Custom handler for results
			resHandler
		);

		var post = 'Mode=' + (_selectionMode == _singleMode ? 'Single' : 'Batch');
		xhr.send('/youpi/process/db/getSelections/', post);
	}

	/*
	 * Function: selectionMethodChanged
	 * _Public_ Method selection has changed in the combobox
	 *
	 */ 
	this.selectionMethodChanged = function() {
		var selNode = document.getElementById(id + '_method_selection_select');
		var newDiv = document.getElementById(id + '_new_image_selection_div');
		var mergeDiv = document.getElementById(id + '_merge_image_selection_div');

		switch (selNode.selectedIndex) {
			case 0:
				// Create a new image selection
				displayOnlyMethodContainer(newDiv);
				break;
			case 1:
				// Merge saved selections
				displayOnlyMethodContainer(mergeDiv);
				break;
			default:
				break;
		}
	}

	/*
	 * Function: deleteSavedSelection
	 * _Public_ Really delete saved image selection by committing changes to DB.
	 *
	 */ 
	this.deleteSavedSelection = function() {
		var div = document.getElementById(id + '_delete_selection_subdiv');
		var sel = div.getElementsByTagName('select')[0];
		var name = sel.options[sel.selectedIndex].text;

		var r = confirm("Are you sure you want to delete the selection '" + name + "'\nfrom the database?");
		if (!r) return;

		var xhr = new HttpRequest(
			div.id,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				removeAllChildrenNodes(div);
				removeAllChildrenNodes(div);
				var p = document.createElement('p');
				p.setAttribute('class', 'done');
				p.appendChild(document.createTextNode("Done. Selection '" + name + "'"));
				p.appendChild(document.createElement('br'));
				p.appendChild(document.createTextNode('deleted.'));
				div.appendChild(p);
			}
		);

		post = 'Name=' + name.replace('+', '%2B');
		// Send HTTP POST request
		xhr.send('/youpi/process/db/delSelection/', post);
	}

	/*
	 * Function: mergeSavedSelections
	 * _Public_ Really merge images selections by committing changes to DB.
	 *
	 */ 
	this.mergeSavedSelections = function() {
		var div = document.getElementById(id + '_merge_selections_subdiv');
		var sel = div.getElementsByTagName('select')[0];
		var name = sel.options[sel.selectedIndex].text;

		var multiSel = new Array();
		var numSelected = 0, opt;
		for (var j=0; j < sel.options.length; j++) {
			opt = sel.options[j];
			if (opt.selected) {
				multiSel[numSelected++] = opt.text;
			}
		}

		var r = confirm("Are you sure you want to merge '" + multiSel +  "'\ninto the current selection?");
		if (!r) return;

		var xhr = new HttpRequest(
			div.id,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				var sels = resp['data'];
				// Ids of images from multi-selection
				var selIdList = new Array();
				// Ids of images in the grid
				var gIdList = new Array();

				for (var j=0; j<multiSel.length; j++) {
					for (var k=0; k<sels.length; k++) {
						if (multiSel[j] == sels[k][0]) {
							selIdList[j] = sels[k][1];	
							break;
						}
					}
				}

				gIdList = _tableWidget.getSelectedRows().split(',');

				// Rebuild grid
				resultHandler(gIdList.concat(selIdList), document.getElementById('_result_grid_div'));

				removeAllChildrenNodes(div);
				removeAllChildrenNodes(div);
				var p = document.createElement('p');
				p.setAttribute('class', 'done');
				p.appendChild(document.createTextNode("Done. Selection(s) merged"));
				p.appendChild(document.createElement('br'));
				p.appendChild(document.createTextNode('into current one.'));
				div.appendChild(p);
			}
		);

		// Get all selections
		var post = 'Mode=' + (_selectionMode == _singleMode ? 'Single' : 'Batch');
		xhr.send('/youpi/process/db/getSelections/', post);
	}

	/*
	 * Function: saveSelection
	 * _Public_ Really save an image selection by committing changes to DB.
	 *
	 * First check that a selection with that name does not 
	 * already exist in DB. If not, call <saveSelectionToDB>.
	 *
	 */ 
	this.saveSelection = function() {
		var textNode = document.getElementById(id + '_save_selection_text');
		var name = textNode.value.replace('+', '%2B');

		if (name.length == 0) {
			alert('Cannot save a selection with an empty name!');
			textNode.focus();
			return;
		}

		// Checks for name availability (does not exits in DB)
		var cnode = document.getElementById(id + '_save_selection_res_div');
		var xhr = new HttpRequest(
			cnode.id,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				removeAllChildrenNodes(cnode);
				var nb = resp['data'].length;
				var p = document.createElement('p');
				if (nb > 0) {
					// Name already exists, ask for overwriting
					var r = confirm("A selection with that name already exists in the database.\nWould you like to overwrite it ?");
					if (!r) return;
				}

				// Saves to DB
				saveSelectionToDB(name);
			}
		);

		// Get name of all saved selections
		post = 'Table=youpi_imageselections&DisplayField=name&Lines=0&Line0Field=name&Line0Cond=is equal to&Line0Text=' + name + '&Hide=&OrderBy=id';

		// Send HTTP POST request
		xhr.send('/youpi/process/preingestion/query/', post);
	}

	/*
	 * Function: saveSelectionToDB
	 * _Public_ Really save an image selection by committing changes to DB.
	 *
	 * Parameters:
	 *
	 * name - string: name of selection to store
	 *
	 */ 
	function saveSelectionToDB(name) {
		var cnode = document.getElementById(id + '_save_selection_res_div');
		var xhr = new HttpRequest(
			cnode.id,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				// Selection saved
				removeAllChildrenNodes(cnode);
				var p = document.createElement('p');
				p.setAttribute('class', 'done');
				p.appendChild(document.createTextNode("Done. Selection saved under"));
				p.appendChild(document.createElement('br'));
				p.appendChild(document.createTextNode("'" + name.replace('%2B', '+') + "'."));
				cnode.appendChild(p);
			}
		);

		// Get name of all saved selections
		post = 'Name=' + name + '&IdList=' + _getListsOfSelections();

		// Send HTTP POST request
		xhr.send('/youpi/process/db/saveSelection/', post);
	}

	/*
	 * Function: addTRLine
	 * Adds a new line with new search criteria
	 *
	 * Parameters:
	 *
	 * afterNode - TR parent DOM node 
	 *
	 */ 
	function addTRLine(afterNode) {
		var tr, td, but;
	
		// DOM node
		afterNode = afterNode || alert('after DOM node not defined!');
	
		// Use a rather unique TR id
		var trid = genID('Line');
		tr = document.createElement('tr');
		tr.setAttribute('id', trid);
		tr.setAttribute('class', 'queryline');

		// Remove button
		td = document.createElement('td');
		if (currentTR > 0) {
			but = document.createElement('input');
			with (but) {
				var nid = genID('ButtonDel');
				setAttribute('id', nid);
				setAttribute('type', 'button');
				// Try to reach and remove TR DOM element
				setAttribute('onclick', _instance_name + ".getTopNode().removeChild(document.getElementById('" + nid + "').parentNode.parentNode)");
				setAttribute('value', '-');
			}
			td.appendChild(document.createTextNode('then  '));
			td.appendChild(but);
		}
		tr.appendChild(td);
	
		// Add button
		td = document.createElement('td');
		but = document.createElement('input');
		with (but) {
			var nid = genID('ButtonAdd');
			setAttribute('id', nid);
			setAttribute('type', 'button');
			setAttribute('onclick', _instance_name + ".addLine(document.getElementById('" + trid + "'));");
			setAttribute('value', '+');
		}
		td.appendChild(but);
		tr.appendChild(td);

		// Builds select with search criteria
		var selNode = getMainCriteriaDOM(currentTR);
		td = document.createElement('td');
		td.appendChild(selNode);
		tr.appendChild(td);

		// Condition
		td = document.createElement('td');
		var cdiv = document.createElement('div');
		cdiv.setAttribute('id', id + '_cond_div_' + currentTR);
		selNode = eval('get' + fields[0] + 'CondSelect')(currentTR);
		cdiv.appendChild(selNode);
		td.appendChild(cdiv);
		tr.appendChild(td);

		// Condition custom DOM (as returned by get{NAME}DOM())
		td = document.createElement('td');
		cdiv = document.createElement('div');
		cdiv.setAttribute('id', id + '_custom_div_' + currentTR);
		td.appendChild(cdiv);
		tr.appendChild(td);

		if (afterNode.nextSibling) {
			afterNode.parentNode.insertBefore(tr, afterNode.nextSibling);
		}
		else {
			afterNode.parentNode.appendChild(tr);
		}

		// Nb result div (per TR line)
		td = document.createElement('td');
		td.setAttribute('style', 'text-align: left; vertical-align: middle');
		var rdiv = document.createElement('div');
		rdiv.setAttribute('id', id + '_nbResults_div_' + currentTR);
		td.appendChild(rdiv);
		tr.appendChild(td);

		// Finally executes appropriate handler for current line
		eval('build' + fields[0] + 'DataWidget')(currentTR);
	
		currentTR++;
	}

	/*
	 * Function: getCondText
	 * Get conditionnal text value selected in ComboBox
	 *
	 * Parameters:
	 *
	 * idx - integer: row identifier 
	 *
	 * Returns:
	 *
	 * String value of selected option
	 *
	 */ 
	function getCondText(idx) {
		var selNode = document.getElementById(id + '_condition_select_' + idx);
		var selOption = selNode.options[selNode.selectedIndex];
		return selOption.text;
	}

	/*
	 * Function: executeQuery
	 * _Public_ Executes server-side SQL query (AJAX query)
	 *
	 * Used to find images and build a selection of images in _single_selection_mode_.
	 *
	 * See Also:
	 *
	 * <sendq>
	 *
	 */ 
	this.executeQuery = function () {
		var output = document.getElementById(id + '_result_div');
		var xhr = new HttpRequest(
			output.id,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				/*
				 * Since saved selections now handle a batch selection mode, data format returned has 
				 * changed and looks like [[id1,id2,...],...]. 
				 * Saved selection-related response misses a 'fields' key.
				 * To keep working with single selection mode, it needs to be converted to [[id1],[id2]...] 
				 * format first.
				 *
				 */
				if (typeof resp['fields'] == 'undefined') {
					var ids = new Array();
					for (var j=0; j < resp['data'][0].length; j++) {
						ids[j] = new Array();
						ids[j][0] = resp['data'][0][j];
					}
					resp['data'] = ids;
				}

				var count = resp['data'].length;
				var d = document.createElement('div');
				// Called twice to prevent a Firebug strange behaviour
				removeAllChildrenNodes(output);
				removeAllChildrenNodes(output);

				// +1 Skip first empty TR node
				var ds = topNode.childNodes[xhr.idResultsIdx+1].getElementsByTagName('div');
				var rdiv;
				for (var j=0; j < ds.length; j++) {
					rdiv = ds[j];	
					if (rdiv.getAttribute('id').search('_nbResults_div_') != -1) {
						break;
					}
				}

				rdiv.setAttribute('style', 'padding: 2px; background-color: lightblue; border: 1px solid #5b80b2; text-align:center; vertical-align: middle;');
				removeAllChildrenNodes(rdiv);
				removeAllChildrenNodes(rdiv);
				rdiv.appendChild(document.createTextNode(count));

				idResults.splice(xhr.idResultsIdx, 1);
				if (idResults[xhr.idResultsIdx]) {
					delete(idResults[xhr.idResultsIdx]);
				}
				idResults[xhr.idResultsIdx] = new Array();
				for (var j=0; j < count; j++) {
					idResults[xhr.idResultsIdx][j] = resp['data'][j]
				}

				xhr.idResultsIdx++;
				if (xhr.idResultsIdx < topNode.childNodes.length-1) {
					// Last query, we want all data
					sendq(xhr.idResultsIdx+1, xhr);
				}
				else {
					// All queries are done, we can display information about images, if any
					if (count > 0) {
						// There are results, call result handler
						var idList = new Array();
						for (var j=0; j < resp['data'].length; j++) {
							idList[j] = resp['data'][j][0];
						}

						showResultCount(count);
						resultHandler(idList, document.getElementById('_result_grid_div'));
					}
					else {
						showResultCount(count);
					}
				}
			}
		);

		// Index of row
		xhr.idResultsIdx = 0;
		sendq(1, xhr);
	}

	/*
	 * Function: showResultCount
	 * Displays number of matches
	 *
	 * Parameters:
	 *
	 *  count - integer: number of matches
	 *
	 * See Also:
	 *
	 * <renderFinalResults>, <executeQuery>
	 *
	 */ 
	function showResultCount(count) {
		var rg = document.getElementById(id + '_result_count_div');
		removeAllChildrenNodes(rg);
		if (count > 0) {
			rg.setAttribute('class', 'result_count');
			rg.appendChild(document.createTextNode(count + (count > 0 ? ' results' : ' result')));
		}
		else {
			rg.setAttribute('class', 'result_count_no_match');
			rg.appendChild(document.createTextNode('No match'));
		}
	}

	/*
	 * Function: selectAll
	 * _Public_ Selects all result entries by calling default or custom  'selectAll' handler
	 *
	 * See Also:
	 *
	 *  <setSelectAllHandler>, <defaultSelectAllHandler>
	 *
	 */ 
	this.selectAll = function() {
		selectAllHandler();
	}
	
	/*
	 * Function: unselectAll
	 * _Public_ unselects all result entries by calling default or custom  'unselectAll' handler
	 *
	 * See Also:
	 *
	 *  <setUnelectAllHandler>, <defaultUnselectAllHandler>
	 *
	 */ 
	this.unselectAll = function() {
		unselectAllHandler();
	}
	
	/*
	 * Function: defaultUnselectAllHandler
	 * Default handler provided for 'unselect All' operation
	 *
	 * See Also:
	 *
	 *  <setUnselectAllHandler>, <unselectAll>
	 *
	 */ 
	function defaultUnselectAllHandler() {
		toggleSelectAll(false);
	}

	/*
	 * Function: setUnselectAllHandler
	 * _Public_ Can be used to set an alternate handler for 'unselect All' operations
	 *
	 * See Also:
	 *
	 *  <setSelectAllHandler>, <selectAll>
	 *
	 */ 
	this.setUnselectAllHandler = function(func) {
		unselectAllHandler = func ? func : defaultUnselectAllHandler;
	}

	/*
	 * Function: toggleSelectAll
	 * (Un)selects all table rows by checking checkboxes
	 *
	 * Parameters:
	 *
	 *  on - boolean: (de)selecting table's rows
	 *
	 */ 
	function toggleSelectAll(on) {
		if (!_tableWidget.rowCount()) {
			alert(imgSelRequiredMsg);
			return;
		}
		_tableWidget.selectAll(on);
	}

	/*
	 * Function: sendq
	 * Builds the SQL query then sends an AJAX query
	 *
	 * This function can be called many times by the <executeQuery> function (iterative step).
	 *
	 * Parameters:
	 *
	 *  k - integer: index to determine row DOM node in table 
	 *  xhr - <HttpRequest> instance used to send query
	 *
	 * See Also:
	 *
	 * <executeQuery>
	 *
	 */ 
	function sendq(k, xhr) {
		var row, rowNode, critText, valueText, params, rid;

		// Display field
		rowNode = topNode.childNodes[k];
		rid = rowNode.getAttribute('id');
		row = rid.substr(rid.search(/\d+$/));

		critNode = document.getElementById(id + '_mainCriteria_select_' + row);
		condNode = document.getElementById(id + '_condition_select_' + row);
		valueNode = document.getElementById(id + '_custom_div_' + row).firstChild;

		// Gets internal prefix for later get + prefix + SQLParams() method call
		critText = critNode.options[critNode.selectedIndex].text;
		for (var k=0; k < labelFields.length; k++) {
			if (labelFields[k] == critText) {
				critText = fields[k];
				break;
			}
		}

		var multiSel = new Array();

		try {
			// Multi-selection in selects elements will be OR'ed when building SQL query (server-side)
			if (valueNode.hasAttribute('size') && valueNode.hasAttribute('multiple')) {
				var numSelected = 0, opt;
				for (var j=0; j < valueNode.options.length; j++) {
					opt = valueNode.options[j];
					if (opt.selected) {
						multiSel[numSelected++] = opt.text.replace('+', '%2B');
					}
				}
				valueText = 'MULTI';
			}
			else {
				valueText = valueNode.options[valueNode.selectedIndex].text.replace('+', '%2B');
			}
		}
		catch(err) {
			// Not a combobox, condiders it's a textbox
			valueText = valueNode.value.replace('+', '%2B');
		}

		params = eval('get' + critText + 'SQLParams')();

		/** SPECIAL CASE **/
		if (params['special']) {
			post = 'Name=' + valueText + '&Mode=Single';
			xhr.send('/youpi/process/db/getSelections/', post);
			return;
		}

		// Replace any '*' wildcard by '%'
		valueText = valueText.replace(/%/g, '%25').replace(/\*/g, '%25');

		post = 'Table=youpi_image&DisplayField=id&Lines=0&Line0Field=' + params['field'] + 
			'&Line0Cond=' + getCondText(row) + '&Line0Text=' + valueText + '&Hide=&OrderBy=id';

		if (multiSel.length > 0) {
			// This is a multi-selection capable combobox
			post += '&MultiSelection=' + multiSel;
		}

		if (params['ftable']) {
			// Complex query
			post += '&Ftable=' + params['ftable'] +
					'&FtableField=' + params['ftable_field'] +
					'&FtableFieldValue=' + valueText +
					'&FtableId=' + params['ftable_id'] +
					'&FkId=' + params['fkid'];
		}

		if (xhr.idResultsIdx > 0) {
			post += '&IdList=';
			if (idResults[xhr.idResultsIdx-1].length > 0) {
				post += idResults[xhr.idResultsIdx-1];
			}
			else {
				post += '-1';
			}
			post += '&IdField=id';
		}
	
		// Send POST HTTP query
		xhr.send('/youpi/process/preingestion/query/', post);
	}

	/*
	 * Function: getMainCriteriaDOM
	 * Sets up a combox box with all the available search criterias
	 *
	 * Parameters:
	 *
	 *  tr_idx - string: id of DOM container element
	 *
	 * Returns:
	 *
	 *  DOM select element
	 *
	 * See Also:
	 *
	 * <fields>, <addTRLine>
	 *
	 */ 
	function getMainCriteriaDOM(tr_idx) {
		var select = document.createElement('select');
		select.setAttribute('id', id + '_mainCriteria_select_' + tr_idx);
		// Call matching handler when selection changes
		select.setAttribute('onchange', _instance_name + '.executeHandler(' + tr_idx + ');');

		var option;
		for (var j=0; j < fields.length; j++) {
			option = document.createElement('option');
			option.setAttribute('value', j);
			option.appendChild(document.createTextNode(labelFields[j]));
			select.appendChild(option);
		}

		return select;
	}

	/*
	 * Function: getAIM
	 * _Public_ Returns AIM instance
	 *
	 * Returns:
	 *
	 *  <AIM> instance
	 *
	 * See Also:
	 *
	 * <renderBatchSelection>, http://www.webtoolkit.info/
	 *
	 */ 
	this.getAIM = function() { return AIM; }

	/*
	 * Handler called before POST file upload
	 *
	 */
	this.getFileUploadStartHandler = function() { return fileUploadStartHandler; }

	function fileUploadStartHandler() {
		// make something useful before submit (onStart)

		var skydiv = document.getElementById(id + '_sky_selections_div');
		var blog = document.getElementById(_instance_name + '_batch_log_div');
		var log = document.getElementById(id + '_upload_log_div');

		skydiv.innerHTML = '';
		document.getElementById(id + '_batch_load_saved_log_div').innerHTML = '';

		if (blog) blog.style.display = 'none';
		log.innerHTML = '';
		log.innerHTML = getLoadingHTML('Uploading file...');

		return true;
	}

	/*
	 * Handler called upon upload completion
	 *
	 */
	this.getFileUploadCompleteHandler = function() { return fileUploadCompleteHandler; }

	/*
	 * Function: fileUploadCompleteHandler
	 * Executes handler, wrapper for the public interface
	 *
	 * Parameters:
	 *
	 * resp - AJAX response
	 *
	 */ 
	function fileUploadCompleteHandler(resp) {
		var r = eval('(' + resp + ')');
		var len = r['length'];
		var exit_code = r['exit_code'];
		var error_msg = r['error_msg'];
		var fileName = r['filename'];
	
		var log = document.getElementById(id + '_upload_log_div');
		log.innerHTML = '';

		var img_name;
		if (exit_code) {
			// Error
			log.style.color = 'red';
			var msg = ['Error: ' + error_msg, 'Exit code: ' + r['exit_code']];
			img_name = 'icon_error.gif';
		}
		else {
			log.style.color = 'green';
			var msg = ['File \'' + fileName + '\' succesfully uploaded (' + r['length'] + ' bytes)', 'Valid XML file detected'];
			img_name = 'icon-yes.gif';
		}

		for (var k=0; k<msg.length; k++) {
			var img = document.createElement('img');
			img.setAttribute('src', '/media/themes/' + guistyle + '/img/admin/' + img_name);
			log.appendChild(img);
			log.appendChild(document.createTextNode(msg[k]));
			log.appendChild(document.createElement('br'));
		}
		if (exit_code) return;

		// View file content
		log.appendChild(document.createTextNode('('));
		var a = document.createElement('a');
		a.setAttribute('target', '_blank');
		a.setAttribute('href', '/youpi/uploadFile/batch/viewContent/' + fileName + '/');
		a.appendChild(document.createTextNode('View file content'));
		log.appendChild(a);
		log.appendChild(document.createTextNode(')'));

		var rdiv = document.createElement('div');
		rdiv.setAttribute('style', 'color: black;');
		rdiv.setAttribute('id', id + '_upload_content_div');
		log.appendChild(rdiv);

		var bdiv = document.getElementById(id + '_batch_sel_div');
		var blog = document.createElement('div');
		blog.setAttribute('id', _instance_name + '_batch_log_div');
		blog.setAttribute('class', 'ims_batch_log_div');
		bdiv.appendChild(blog);

		var xhr = new HttpRequest(
			rdiv.id,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				img_name = 'icon-yes.gif';
				var res = resp['result'];
				rdiv.innerHTML = '';
				rdiv.style.color = 'green';
				var img = document.createElement('img');
				img.setAttribute('src', '/media/themes/' + guistyle + '/img/admin/' + img_name);
				rdiv.appendChild(img);
				rdiv.appendChild(document.createTextNode('Found ' + res['nbSelections'] + ' selections'));

				var sel = res['selections'];
				var total = 0;
				// Reset batch selections
				_batchModeSelections.length = 0;

				for(var k=0; k<sel.length; k++) {
					rdiv.appendChild(document.createElement('br'));
					rdiv.appendChild(document.createTextNode(k+1 + '. Selection ' + sel[k]['name'] + ' contains '));
					var link = document.createElement('a');
					link.setAttribute('href', '#');
					link.setAttribute('onclick', _instance_name + ".viewBatchSelection('" + encodeURI(sel[k]['xml']) + "');");
					link.appendChild(document.createTextNode(sel[k]['count'] + ' images'));
					rdiv.appendChild(link);
					_batchModeSelections[k] = sel[k]['idList'];
					total += sel[k]['count'];
				}	
				rdiv.appendChild(document.createElement('br'));
				rdiv.appendChild(document.createTextNode('Total: [ ' + total + ' images ]'));

				// Load sky map
				_displaySkyVisualization(fileName);
			}
		);

		// Get all ids of images
		post = 'Filename=' + fileName;

		// Send HTTP POST request
		xhr.setBusyMsg('Parsing XML content');
		xhr.send('/youpi/uploadFile/batch/parseContent/', post);
	}

	/*
	 * Function: _displaySkyVisualization
	 * Display sky visualization widget
	 *
	 * Parameters:
	 *
	 * fileName - string: name of XML file to parse to retreive content
	 *
	 */ 
	function _displaySkyVisualization(fileName) {
		if (!document.getElementById(_instance_name + '_batch_display_sky_check').checked) {
			if (!document.getElementById(_instance_name + '_batch_sky_compute_all_check').checked)
				return;
			else {
				alert('You can\'t plot images center if sky visualisation is unchecked!')
				return;
			}
		}

		var post;
		if (typeof fileName == 'undefined') {
			// Trying to plot sky selections from saved selection data
			post = 'Selections=' + _getListsOfSelections();
		}
		else {
			// Trying to plot sky selections from XML file content
			post = 'Filename=' + fileName;
			if (document.getElementById(_instance_name + '_batch_sky_compute_all_check').checked)
				post += '&PlotCenter=1';
		}

		var skydiv = document.getElementById(id + '_sky_selections_div');
		var xhr2 = new HttpRequest(
			skydiv.id,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				var a = document.createElement('a');
				a.setAttribute('href', resp['imgName']);
				a.setAttribute('target', '_blank');
				var img = document.createElement('img');
				img.setAttribute('src', resp['tnName']);
				skydiv.innerHTML = '';
				a.appendChild(img);
				skydiv.appendChild(a);
			}
		);

		// Send HTTP POST request
		xhr2.setBusyMsg('Loading sky visualization');
		xhr2.send('/youpi/plot/sky/selections/', post);
	}

	/*
	 * Function: viewBatchSelection
	 * Display a selection's content into a new page
	 *
	 * Parameters:
	 *
	 * xml - XML data selection
	 *
	 */ 
	this.viewBatchSelection = function(xml) {
		var log = document.getElementById(_instance_name + '_batch_log_div');
		log.style.display = 'block';

		var xhr = new HttpRequest(
			log.id,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				log.innerHTML = '';
				var pre = document.createElement('pre');
				log.appendChild(pre);
				pre.appendChild(document.createTextNode('Images in ' + resp['name'] + ' selection:'));
				pre.appendChild(document.createElement('br'));

				var len = resp['data'].length;
				for (var k=0; k < len; k++) {
					pre.appendChild(document.createTextNode(resp['data'][k][0] + ' in ' + resp['data'][k][1]));
					pre.appendChild(document.createElement('br'));
				}
			}	
		);

		// Get all ids of images
		post = 'XML=' + xml;

		// Send HTTP POST request
		xhr.setBusyMsg('Retreiving selection content');
		xhr.send('/youpi/uploadFile/batch/viewSelection/', post);
	}

	/*
	 * Return a DOM tr node
	 * Wrapper for the public interface
	 *
	 */
	this.addLine = function(afterNode) {
		addTRLine(afterNode);
	}

	// Main entry point
	render();
}
