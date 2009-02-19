/*
 * Class: ImageSelector
 * Widget that allows image selection.
 *
 * External Dependancies:
 *  common.js - <Logger>
 *  prototype.js - Enhanced Javascript library
 *  scriptaculous.js - Visual effects library
 *
 * Constructor Parameters:
 *  container - string or DOM node: name of parent block container
 *  options - object: options parsed before rendering widget
 *
 * Available Options:
 *  editing - boolean: whether to display options related to edition (save, delete, merge) (default: true)
 *  help - boolean: whether to display tooltips (default: true)
 *  dropzone - boolean: whether to show the drop zone (default: false)
 *
 * Signals:
 *  imageSelector:loaded - signal emitted when the image selector is fully loaded (i.e after AJAX initial queries have returned)
 *
 */
function ImageSelector(container, options)
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
	 * Var: _container
	 * Parent DOM container
	 *
	 */ 
	var _container = $(container);
	/*
	 * Var: id
	 * Unique instance identifier
	 *
	 */ 
	var id = 'IMS_' + Math.floor(Math.random() * 999999);


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
	 * Var: _tags;
	 * Hash - Available tags in drop zone (used only if the dropzone option is true)
	 *
	 */ 
	var _tags = $H();
	/*
	 * Var: _options;
	 * Hash - Image selector options
	 *
	 */ 
	var _options = $H({
		editing: true,
		help: true,
		dropzone: false
	});
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
	 * Var: _selectAllHandler
	 * Default handler for 'Select All' operation
	 *
	 */
	var _selectAllHandler = _defaultSelectAllHandler;
	/*
	 * Var: _unselectAllHandler
	 * Default handler for 'Unselect All' operation
	 *
	 */
	var _unselectAllHandler = _defaultUnselectAllHandler;
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
			var d = new Element('DIV');
			var iframe = new Element('iframe', {style: 'display: none;', src: 'about:blank', id: n, name: n});
			iframe.observe('load', function() {
				AIM.loaded(n);
			});
			d.update(iframe);
			document.body.insert(d);
	
			var i = $(n);
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
			var i = $(id);
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
		var curSelId = $(id + '_mainCriteria_select_' + tr_idx);
		var selOption = curSelId.options[curSelId.selectedIndex];

		// Loads matching conditional combo box
		var condDiv = $(id + '_cond_div_' + tr_idx);
		var selNode = eval('get' + fields[selOption.value] + 'CondSelect')(tr_idx);
		removeAllChildrenNodes(condDiv);
		condDiv.insert(selNode);

		// Now call matching handler
		eval('build' + fields[selOption.value] + 'DataWidget')(tr_idx);
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
	 * Function: _defaultSelectAllHandler
	 * Default handler provided for 'select All' operation
	 *
	 * See Also:
	 *
	 *  <setSelectAllHandler>, <selectAll>
	 *
	 */ 
	function _defaultSelectAllHandler() {
		_toggleSelectAll(true);
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
		_selectAllHandler = func ? func : _defaultSelectAllHandler;
	}


	// Group: Rendering Functions
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Function: _render
	 * Initial rendering step
	 *
	 */ 
	function _render() {
		if (options) {
			if (typeof options != 'object') {
				throw '_render: options must be an object';
				return;
			}
			_options.update(options);
		}

		_container.addClassName('imageSelector');
		// Container for new image selection
		var	topDiv = new Element('div', {id: id + '_new_image_selection_div'});
		_container.insert(topDiv);
		renderCreateNewImageSelection(topDiv);
	}

	/*
	 * Function: _setupSlots
	 * Defines slots to handle external signals
	 *
	 */ 
	function _setupSlots() {
		// Slots for signals
		document.observe('tagPanel:tagDroppedOnZone', function(event) {
			// Do nothing if not concerned
			if (!_options.get('dropzone')) return;

			_tags.set(event.memo.name, true)
			$(id + '_dropzone_commit_div').appear();
		});

		document.observe('tagPanel:tagRemovedFromZone', function(event) {
			// Do nothing if not concerned
			if (!_options.get('dropzone')) return;

			_tags.unset(event.memo);
			_tags.keys().length ? $(id + '_dropzone_commit_div').appear() : $(id + '_dropzone_commit_div').fade();
		});

		document.observe('tagPanel:tagDeleted', function(event) {
			// Do nothing if not concerned
			if (!_options.get('dropzone')) return;

			$(id + '_dropzone_div').select('.tagwidget').each(function(tag) {
				if (tag.innerHTML == event.memo) {
					tag.remove();
					_tags.unset(event.memo);
					throw $break;
				}
			});
		});

		document.observe('tagPanel:tagUpdated', function(event) {
			// Do nothing if not concerned
			if (!_options.get('dropzone')) return;

			$(id + '_dropzone_div').select('.tagwidget').each(function(tag) {
				if (tag.innerHTML == event.memo.oldname) {
					tag.update(event.memo.name);
					tag.writeAttribute('style', event.memo.style);
					throw $break;
				}
			});
		});
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
				// FIXME
		//		_tableWidget.getRoot().addClassName('table_imageSelector');
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
		var single_div = new Element('div', {id: id + '_single_sel_div'}).setStyle({width: '100%'});

		var div = new Element('div');
		div.setAttribute('class', 'headerText');
		div.insert(caption);
		var snb = new Element('span');
		snb.setAttribute('style', 'font-weight: bold;');
		snb.insert(nbRes);
		div.insert(snb);
		div.insert(' images those for which:');
		single_div.insert(div);

		// Table
		topNode = new Element('table');
		var tab = topNode;
		var tr = new Element('tr');
		tab.insert(tr);
		single_div.insert(tab);
		cNode.insert(single_div);

		addTRLine(tr);

		// Execute query
		div = new Element('div', {style: 'text-align: left'});
		var sub = new Element('input', {
				type: 'button',
				value: 'Find images!'
		});
		sub.observe('click', function() {
			_executeQuery();
		});
		div.insert(sub);
		single_div.insert(div);

		// Div that display results count
		div = new Element('div');
		div.setAttribute('id', id + '_result_count_div');
		single_div.insert(div);

		// Result grid
		div = new Element('div');
		div.setAttribute('id', '_result_grid_div');
		div.setAttribute('style', 'width: 100%; height: 90%;');
		single_div.insert(div);

		// Result div
		div = new Element('div');
		div.setAttribute('id', id + '_result_div');
		div.setAttribute('style', 'height: 100%; width: 100%; overflow: hidden;');
		single_div.insert(div);
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
		var batch_div = new Element('div');
		batch_div.setAttribute('id', id + '_batch_sel_div');

		var form = new Element('form', {action: '/youpi/uploadFile/', enctype: 'multipart/form-data', method: 'post'});
		form.observe('submit', function() {
			return AIM.submit(form, {onStart: _fileUploadStartHandler, onComplete: _fileUploadCompleteHandler})
		});

		var xl = new Element('label');
		xl.insert('Select an XML file to upload: ');

		var filei = new Element('input');
		filei.setAttribute('type', 'file');
		filei.setAttribute('name', 'xmlfile');
		xl.insert(filei);

		var subi = new Element('input');
		subi.setAttribute('style', 'margin-left: 10px;');
		subi.setAttribute('type', 'submit');
		subi.setAttribute('value', 'Upload and check file');

		form.insert(xl);
		form.insert(subi);

		batch_div.insert(form);

		// for saved selections
		var sdiv = new Element('div');
		sdiv.setAttribute('id', id + '_batch_load_saved_sel_div');
		batch_div.insert(sdiv);

		var r = new Element('div');
		r.setAttribute('style', 'color: green; width: 70%; background-color: white; float: left; margin-right: 30px;');
		r.setAttribute('id', id + '_upload_log_div');
		batch_div.insert(r);

		r = new Element('div');
		r.setAttribute('id', id + '_sky_selections_div');
		r.setAttribute('title', 'Click on image to see larger version');
		batch_div.insert(r);

		cNode.insert(batch_div);
	}

	/*
	 * Function: _handlerMergeSelections
	 * 'Merge selections' Dropdown box custom handler
	 *
	 */ 
	function _handlerMergeSelections() {
		_showMergeSelectionsBox(this.getContentNode());
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
		var div = new Element('div');
		div.setAttribute('class', 'modeOptions');

		switch(_selectionMode) {
			case _singleMode:
				// Merge saved selections
				if (_options.get('editing')) {
					var dmerge = new DropdownBox(div, 'Merge with selection');
					dmerge.setOnClickHandler(function() {
						if (dmerge.isOpen()) 
							_handlerMergeSelections.bind(dmerge)();
					});
				}

				// Select all
				sub = new Element('input', {
								style: 'margin-right: 10px;',
								type: 'button',
								value: 'Select all'
				});
				sub.observe('click', function() {
					_selectAllHandler();
				});
				div.insert(sub);

				// Unselect all
				sub = new Element('input', { type: 'button', value: 'Unselect all' });
				sub.observe('click', function() {
					_unselectAllHandler();
				});
				div.insert(sub);
				break;

			case _batchMode:
				div.insert(_createCheckBox(id + '_batch_display_sky_check', false, 'Display sky visualization'));
				div.insert(_createCheckBox(id + '_batch_sky_compute_all_check', false, 'Plot all images points, not only selections (slower)'));
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
		var s = new Element('div', {style: 'color: white; margin-left: 10px; margin-right: 5px;'});
		var input = new Element('input', { 'id': id, type: 'checkbox' });
		if (checked)
			input.setAttribute('checked', 'checked');

		var lab = new Element('label');
		lab.insert('   ' + label);

		s.insert(input);
		s.insert(lab);

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
		var div = new Element('div');
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
		var bdiv = new Element('div');
		bdiv.setAttribute('id', id + '_selection_box_div');
		bdiv.setAttribute('class', 'controlPanel');

		// Save selection
		div = new Element('div', {'id': id + '_save_selection_div'});
		var sub = new DropdownBox(div, 'Save selection');
		sub.setOnClickHandler(_handlerSaveSelectionAs.bind(sub));
		bdiv.insert(div);

		// Delete existing selection
		div = new Element('div', {'id': id + '_delete_selection_div'});
		sub = new DropdownBox(div, 'Delete selection');
		sub.setOnClickHandler(_handlerDeleteExistingSelection.bind(sub));
		bdiv.insert(div);

		return bdiv;
	}

	/*
	 * Function: _handlerSaveSelectionAs
	 * 'Save selection' Dropdown box custom handler
	 *
	 */ 
	function _handlerSaveSelectionAs() {
		_showSaveSelectionBox(this.getContentNode());
	}

	/*
	 * Function: _handlerDeleteExistingSelection
	 * 'Delete selection' Dropdown box custom handler
	 *
	 */ 
	function _handlerDeleteExistingSelection() {
		_showDeleteSelectionBox(this.getContentNode());
	}

	/*
	 * Function: renderCreateNewImageSelection
	 * Queries number of images ingested into DB and initiates widget rendering
	 *
	 * Parameters:
	 *   containerNode - DOM node parent container
	 *
	 */ 
	function renderCreateNewImageSelection(containerNode) {
		var xhr = new HttpRequest(
			containerNode,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				var nb = resp['Total'];
				containerNode.update();
				addImageQueryForm(containerNode, nb);
				// Emit signal when widget is fully loaded
				document.fire('imageSelector:loaded');
			}
		);

		// Send HTTP POST request
		xhr.send('/youpi/ingestion/imgCount/');
	}

	/*
	 * Function: _showDeleteSelectionBox
	 * Displays selection box used for deleting DB image selections
	 *
	 * Parameters:
	 *  container - string or DOM node: parent container
	 *
	 */ 
	function _showDeleteSelectionBox(container) {
		var sub = $(id + '_delete_selection_subdiv');

		if (!sub) {
			sub = new Element('div');
			sub.setAttribute('id', id + '_delete_selection_subdiv');
			sub.setAttribute('class', 'show');
			container.insert(sub);
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
				var p = new Element('p');
				p.setAttribute('class', 'error');
				p.insert('No saved selections found.');
				p.insert(new Element('br'));
				p.insert('Nothing to delete.');
				sub.insert(p);
				return;
			}

			var options = [];
			for (var k=0; k < resp['data'].length; k++) {
				options[k] = resp['data'][k][0];
			}
			var sel = getSelect(id + '_del_selection_combo', options);
			sub.insert(sel);

			var del = new Element('input', {type: 'button', value: 'Delete!'});
			del.observe('click', function() {
				_deleteSavedSelection();
			});
			sub.insert(del);
		});
	}

	/*
	 * Function: _showMergeSelectionsBox
	 * Displays selection box used for merging DB image selections
	 *
	 * Parameters:
	 *  container - string or DOM node: parent container
	 *
	 */ 
	function _showMergeSelectionsBox(container) {
		if (!_getListsOfSelections()) {
			container.update(imgSelRequiredMsg);
			return;
		}
		container.update();
		var sub = $(id + '_merge_selections_subdiv');
		
		if (!sub) {
			sub = new Element('div');
			sub.setAttribute('id', id + '_merge_selections_subdiv');
			sub.setAttribute('class', 'show');
			container.insert(sub);
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
				var p = new Element('p');
				p.setAttribute('class', 'error');
				p.insert('No saved selections found.');
				p.insert(new Element('br'));
				p.insert('Nothing to merge.');
				sub.insert(p);
				return;
			}

			var p = new Element('p');
			p.setAttribute('style', 'font-style: italic');
			p.insert(len + ' ' + (len > 1 ? 'selections' : 'selection') + ' available');
			sub.insert(p);

			var options = []
			for (var k=0; k < len; k++) {
				options[k] = resp['data'][k][0];
			}
			var combosize = options.length > 5 ? 8 : options.length
			var sel = getSelect(id + '_merge_selections_combo', options, combosize);
			sub.insert(sel);

			var del = new Element('input', {type: 'button', value: 'Merge!'});
			del.observe('click', function() {
				_mergeSavedSelections();
			});
			sub.insert(del);
		});
	}

	/*
	 * Function: _showSaveSelectionBox
	 * Displays selection box used for saving DB image selections
	 *
	 * Parameters:
	 *  container - string or DOM node: parent container
	 *
	 */ 
	function _showSaveSelectionBox(container) {
		if (!_getListsOfSelections()) {
			container.update(imgSelRequiredMsg);
			return;
		}

		container.update();
		var sub = $(id + '_save_selection_subdiv');

		if (!sub) {
			sub = new Element('div');
			sub.setAttribute('id', id + '_save_selection_subdiv');
			sub.setAttribute('class', 'show');

			var txt = new Element('input');
			txt.setAttribute('style', 'float: left; margin-right: 5px;');
			txt.setAttribute('id', id + '_save_selection_text');
			txt.setAttribute('type', 'text');
			sub.insert(txt);

			var save = new Element('input', {type: 'button', value: 'Save!'});
			save.observe('click', function() {
				_saveSelection();
			});
			sub.insert(save);

			var res = new Element('div');
			res.setAttribute('id', id + '_save_selection_res_div');
			res.setAttribute('style', 'vertical-align: middle');
			sub.insert(res);

			container.insert(sub);

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
				var nText = $(id + '_save_selection_text');
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
		var output = $(id + '_custom_div_' + tr_idx);

		var xhr = new HttpRequest(
			output.id,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				// Rendering
				removeAllChildrenNodes(output);
				var selNode = getSelect(id + '_object_select_' + tr_idx, resp['data'], 6);
				output.insert(selNode);
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
		var output = $(id + '_custom_div_' + tr_idx);

		var xhr = new HttpRequest(
			output.id,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				// Rendering
				removeAllChildrenNodes(output);
				var selNode = getSelect(id + '_ingestionId_select_' + tr_idx, resp['data']);
				output.insert(selNode);
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
		var output = $(id + '_custom_div_' + tr_idx);

		var xhr = new HttpRequest(
			output.id,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				// Rendering
				removeAllChildrenNodes(output);
				var selNode = getSelect(id + '_channel_select_' + tr_idx, resp['data'], 6);
				output.insert(selNode);
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
		var output = $(id + '_custom_div_' + tr_idx);

		var xhr = new HttpRequest(
			output.id,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				// Rendering
				removeAllChildrenNodes(output);
				var selNode = getSelect(id + '_instrument_select_' + tr_idx, resp['data']);
				output.insert(selNode);
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
		var output = $(id + '_custom_div_' + tr_idx);

		var xhr = new HttpRequest(
			output.id,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				// Rendering
				removeAllChildrenNodes(output);
				var selNode = getSelect(id + '_run_select_' + tr_idx, resp['data'], 6);
				output.insert(selNode);
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
		var output = $(id + '_custom_div_' + tr_idx);

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
					var selNode = new Element('select');
					selNode.setAttribute('id', selid);
					option = new Element('option');
					option.setAttribute('value', 0);
					option.insert('-- No saved selection in database --');
					selNode.insert(option);
				}
				output.insert(selNode);
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
		var output = $(id + '_custom_div_' + tr_idx);
		var txtNode = new Element('input');
		txtNode.setAttribute('type', 'text');

		removeAllChildrenNodes(output);
		output.insert(txtNode);
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
		var output = $(id + '_custom_div_' + tr_idx);
		var txtNode = new Element('input');
		txtNode.setAttribute('type', 'text');

		removeAllChildrenNodes(output);
		output.insert(txtNode);
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
		var output = $(id + '_custom_div_' + tr_idx);
		var txtNode = new Element('input');
		txtNode.setAttribute('type', 'text');

		removeAllChildrenNodes(output);
		output.insert(txtNode);
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
	 *  string - array of selections; null if no selection
	 *
	 */ 
	function _getListsOfSelections() {
		switch(_selectionMode) {
			case _singleMode:
				var sel = _tableWidget.getSelectedColsValues();
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
		var msel = $(id + '_image_mode_sel');
		/* 
		 * mode = 0 - SM
		 * mode = 1 - BM
		 */
		var mode = msel.selectedIndex;
		var sdiv = $(id + '_single_sel_div');
		var bdiv = $(id + '_batch_sel_div');

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

		var optdiv = $(id + '_mode_options_div');
		optdiv.innerHTML = '';
		optdiv.insert(_getOptionsToolbar());

		var dropdiv = $(id + '_dropzone_div');
		dropdiv.update();
		if (_options.get('dropzone'))
			dropdiv.appear();

		var tipdiv = $(id + '_mode_options_tip_div');
		tipdiv.update();
		if (_options.get('help'))
			tipdiv.insert(_getContextTip());
	}

	/*
	 * Function: _updateBatchSavedSelectionArea 
	 * Checks if batch saved selections are available
	 *
	 */ 
	function _updateBatchSavedSelectionArea() {
		var	seldiv = $(id + '_batch_load_saved_sel_div');
	
		var xhr = new HttpRequest(
			seldiv,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				var data = resp['data'];
				seldiv.innerHTML = '';

				var blog = new Element('div');
				blog.setAttribute('id', id + '_batch_load_saved_log_div');
				blog.setAttribute('style', 'float: left;');
				seldiv.insert(blog);

				if (!data.length) return;
	
				var r = new Array();
				for (var k=0; k < data.length; k++) {
					r[k] = data[k][0];
				}
	
				seldiv.insert('Or load a saved selection: ');
				seldiv.insert(getSelect(id + '_batch_load_saved_sel', r));
	
				var lbut = new Element('input', {style: 'margin-left: 10px;', type: 'button', value: 'Load'});
				lbut.observe('click', function() {
					_loadBatchSavedSelection();
				});
		
				seldiv.insert(lbut);
			}
		);
	
		var post = 'Mode=Batch';
		xhr.send('/youpi/process/db/getSelections/', post);
	}

	/*
	 * Function: _loadBatchSavedSelection 
	 * Loads a batch saved selection
	 *
	 */ 
	function _loadBatchSavedSelection() {
		var	div = $(id + '_batch_load_saved_log_div');
		var sel = $(id + '_batch_load_saved_sel');
		var name = sel.options[sel.selectedIndex].text;
		$(id + '_upload_log_div').innerHTML = '';
		$(id + '_sky_selections_div').innerHTML = '';

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
		var sdiv = new Element('div');
		sdiv.setAttribute('class', 'image_mode');
		var modes = ['Single selection', 'Batch selection'];
		var lab = new Element('label');
		lab.insert('Selection mode: ');

		var msel = getSelect(id + '_mode_sel', modes);
		msel.setAttribute('id', id + '_image_mode_sel');
		msel.observe('change', function() {
			_swapSelectionMode();
		});

		sdiv.insert(lab);
		lab.insert(msel);
		cNode.insert(sdiv);

		var bltab = new Element('table');
		bltab.setAttribute('class', 'optionsPanel');
		cNode.insert(bltab);

		var tr = new Element('tr');
		bltab.insert(tr);

		var td = new Element('td');
		var ediv = new Element('div');
		if (_options.get('editing'))
			ediv.insert(_getEditSelectionBox());
		td.insert(ediv);

		var optdiv = new Element('div');
		optdiv.setAttribute('id', id + '_mode_options_div');
		td.insert(optdiv);

		var dropdiv = new Element('div', {id: id + '_dropzone_div'});
		dropdiv.addClassName('dropzone').addClassName('dropzoneEmbedded');
		dropdiv.insert('Drag tag here');
		td.insert(dropdiv.hide());

		var comdiv = new Element('div', {id: id + '_dropzone_commit_div'});
		['dropzone', 'dropzoneEmbedded', 'commitEmbedded'].each(function(cls) {
			comdiv.addClassName(cls);
		});
		td.insert(comdiv.hide());

		var tipdiv = new Element('div');
		tipdiv.setAttribute('id', id + '_mode_options_tip_div');
		td.insert(tipdiv);

		tr.insert(td);

		td = new Element('td', {style: 'width: 75%;'});
		tr.insert(td);

		_addDropZoneCommitButtons();

		renderSingleSelection(td, nbRes);
		renderBatchSelection(td, nbRes);

		// Default mode: single selection
		_swapSelectionMode();
	}

	/*
	 * Function: _addDropZoneCommitButtons
	 * Adds _mark_ and _unmark_ commit buttons to the drop zone
	 *
	 */ 
	function _addDropZoneCommitButtons() {
		var c = $(id + '_dropzone_commit_div');
		var markb = new Element('input', {type: 'button', value: 'Mark'});
		markb.observe('click', function() {
			_markActiveSelection(true);
		});
		var unmarkb = new Element('input', {type: 'button', value: 'Unmark'});
		unmarkb.observe('click', function() {
			_markActiveSelection(false);
		});
		c.insert(unmarkb).insert(markb);
	}

	/*
	 * Function: _markActiveSelection
	 * Marks active image selection with tags in drop zone
	 *
	 * Parameters:
	 *  mark - boolean: tag images if true, unmark them if false
	 *
	 */ 
	function _markActiveSelection(mark) {
		if (typeof mark != 'boolean') {
			throw "_markActiveSelection: mark must be a boolean"
			return;
		}

		var sel = _getListsOfSelections();
		if (!sel) {
			alert("Can't " + (mark ? '' : 'un') + "mark an empty selection!");
			return;
		}

		var c = $(id + '_dropzone_commit_div');
		var xhr = new HttpRequest(
			c,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				if (resp.Error) {
					console.warn(resp.Error);
					return;
				}

				var log = new Logger(c);
				c.update();
				log.msg_ok('Current selection has been <b>' + (mark ? '' : 'un') + 'marked</b> successfully.');
				c.fade({ 
					delay: 1.5,
					afterFinish: function() {
						c.update();
						c.appear();
						_addDropZoneCommitButtons();
					}
				});
			}
		);

		var post = {
			IdList: sel,
			Tags: _tags.keys().toJSON()
		};

		// Send HTTP POST request
		xhr.setBusyMsg('Committing');
		xhr.send('/youpi/tags/' + (mark ? '' : 'un') + 'mark/', $H(post).toQueryString());
	}

	/*
	 * Function: getDropZone
	 * Returns DOM container used as a drop zone
	 *
	 * Returns:
	 *  container - DOM node container or null if options.dropzone is false
	 *
	 */ 
	this.getDropZone = function() {
		return _options.get('dropzone') ? $(id + '_dropzone_div') : null;
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
		var selNode = $(id + '_method_selection_select');
		var newDiv = $(id + '_new_image_selection_div');
		var mergeDiv = $(id + '_merge_image_selection_div');

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
	 * Function: _deleteSavedSelection
	 * Effectively deletes saved image selection by committing changes to DB.
	 *
	 */ 
	function _deleteSavedSelection() {
		var div = $(id + '_delete_selection_subdiv');
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
				var p = new Element('p');
				p.setAttribute('class', 'done');
				p.insert("Done. Selection '" + name + "'");
				p.insert(new Element('br'));
				p.insert('deleted.');
				div.insert(p);
			}
		);

		post = 'Name=' + name.replace('+', '%2B');
		// Send HTTP POST request
		xhr.send('/youpi/process/db/delSelection/', post);
	}

	/*
	 * Function: _mergeSavedSelections
	 * Effectively merges images selections by committing changes to DB.
	 *
	 */ 
	function _mergeSavedSelections() {
		var div = $(id + '_merge_selections_subdiv');
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

				gIdList = _tableWidget.getSelectedColsValues().split(',');

				// Rebuild grid
				resultHandler(gIdList.concat(selIdList), $('_result_grid_div'));

				removeAllChildrenNodes(div);
				removeAllChildrenNodes(div);
				var p = new Element('p');
				p.setAttribute('class', 'done');
				p.insert("Done. Selection(s) merged");
				p.insert(new Element('br'));
				p.insert('into current one.');
				div.insert(p);
			}
		);

		// Get all selections
		var post = 'Mode=' + (_selectionMode == _singleMode ? 'Single' : 'Batch');
		xhr.send('/youpi/process/db/getSelections/', post);
	}

	/*
	 * Function: _saveSelection
	 * Effectively Really save an image selection by committing changes to DB.
	 *
	 * First check that a selection with that name does not 
	 * already exist in DB. If not, call <_saveSelectionToDB>.
	 *
	 */ 
	function _saveSelection() {
		var textNode = $(id + '_save_selection_text');
		var name = textNode.value.replace('+', '%2B');

		if (name.length == 0) {
			alert('Cannot save a selection with an empty name!');
			textNode.focus();
			return;
		}

		// Checks for name availability (does not exits in DB)
		var cnode = $(id + '_save_selection_res_div');
		var xhr = new HttpRequest(
			cnode.id,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				removeAllChildrenNodes(cnode);
				var nb = resp['data'].length;
				var p = new Element('p');
				if (nb > 0) {
					// Name already exists, ask for overwriting
					var r = confirm("A selection with that name already exists in the database.\nWould you like to overwrite it ?");
					if (!r) return;
				}

				// Saves to DB
				_saveSelectionToDB(name);
			}
		);

		// Get name of all saved selections
		post = 'Table=youpi_imageselections&DisplayField=name&Lines=0&Line0Field=name&Line0Cond=is equal to&Line0Text=' + name + '&Hide=&OrderBy=id';

		// Send HTTP POST request
		xhr.send('/youpi/process/preingestion/query/', post);
	}

	/*
	 * Function: _saveSelectionToDB
	 * Saves an image selection by committing changes to DB.
	 *
	 * Parameters:
	 *
	 * name - string: name of selection to store
	 *
	 */ 
	function _saveSelectionToDB(name) {
		var cnode = $(id + '_save_selection_res_div');
		var sels = _getListsOfSelections();

		var xhr = new HttpRequest(
			cnode.id,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				// Selection saved
				cnode.update();
				var p = new Element('p', {'class': 'done'}).insert("Done. Selection saved under<br/>");
				p.insert("'" + name.replace('%2B', '+') + "'.");
				cnode.insert(p);

				if (_selectionMode == _batchMode && eval(sels).length == 1) {
					alert('Please note that your list of selections only contains one selection,\n' +
						'so the selection you just saved will only be accessible from the single\n' +
						'selection mode!');
				}
			}
		);

		// Get name of all saved selections
		post = 'Name=' + name + '&IdList=' + sels;

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
		afterNode = $(afterNode);
	
		// Use a rather unique TR id
		var trid = genID('Line');
		tr = new Element('tr');
		tr.setAttribute('id', trid);
		tr.setAttribute('class', 'queryline');

		// Remove button
		td = new Element('td');
		if (currentTR > 0) {
			but = new Element('input', {id: genID('ButtonDel'),
										type: 'button',
										value: '-'
			});
			// Removes line
			but.observe('click', function(event) {
				event.element().up('tr').remove();
			});
			td.insert('then  ');
			td.insert(but);
		}
		tr.insert(td);
	
		// Add button
		td = new Element('td');
		but = new Element('input');
		with (but) {
			var nid = genID('ButtonAdd');
			setAttribute('id', nid);
			setAttribute('type', 'button');
			// Adds a new line
			but.observe('click', function(event) {
				addTRLine(event.element().up('tr'));
			});
			setAttribute('value', '+');
		}
		td.insert(but);
		tr.insert(td);

		// Builds select with search criteria
		var selNode = getMainCriteriaDOM(currentTR);
		td = new Element('td');
		td.insert(selNode);
		tr.insert(td);

		// Condition
		td = new Element('td');
		var cdiv = new Element('div');
		cdiv.setAttribute('id', id + '_cond_div_' + currentTR);
		selNode = eval('get' + fields[0] + 'CondSelect')(currentTR);
		cdiv.insert(selNode);
		td.insert(cdiv);
		tr.insert(td);

		// Condition custom DOM (as returned by get{NAME}DOM())
		td = new Element('td');
		cdiv = new Element('div');
		cdiv.setAttribute('id', id + '_custom_div_' + currentTR);
		td.insert(cdiv);
		tr.insert(td);

		if (afterNode.nextSibling) {
			afterNode.parentNode.insertBefore(tr, afterNode.nextSibling);
		}
		else {
			afterNode.parentNode.insert(tr);
		}

		// Nb result div (per TR line)
		td = new Element('td');
		td.setAttribute('style', 'text-align: left; vertical-align: middle');
		var rdiv = new Element('div');
		rdiv.setAttribute('id', id + '_nbResults_div_' + currentTR);
		td.insert(rdiv);
		tr.insert(td);

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
		var selNode = $(id + '_condition_select_' + idx);
		var selOption = selNode.options[selNode.selectedIndex];
		return selOption.text;
	}

	/*
	 * Function: _executeQuery
	 * _Public_ Executes server-side SQL query (AJAX query)
	 *
	 * Used to find images and build a selection of images in _single_selection_mode_.
	 *
	 * See Also:
	 *
	 * <sendq>
	 *
	 */ 
	function _executeQuery() {
		var output = $(id + '_result_div');
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
				var d = new Element('div');
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
				rdiv.insert(count);

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
						resultHandler(idList, $('_result_grid_div'));
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
	 * <renderFinalResults>, <_executeQuery>
	 *
	 */ 
	function showResultCount(count) {
		var rg = $(id + '_result_count_div');
		removeAllChildrenNodes(rg);
		if (count > 0) {
			rg.setAttribute('class', 'result_count');
			rg.insert(count + (count > 0 ? ' results' : ' result'));
		}
		else {
			rg.setAttribute('class', 'result_count_no_match');
			rg.insert('No match');
			var g = $('_result_grid_div');
			if (g) g.update();
		}
	}

	/*
	 * Function: selectAll
	 * _Public_ Selects all result entries by calling default or custom  'selectAll' handler
	 *
	 * See Also:
	 *
	 *  <setSelectAllHandler>, <_defaultSelectAllHandler>
	 *
	 */ 
	this.selectAll = function() {
		_selectAllHandler();
	}
	
	/*
	 * Function: unselectAll
	 * _Public_ unselects all result entries by calling default or custom  'unselectAll' handler
	 *
	 * See Also:
	 *
	 *  <setUnelectAllHandler>, <_defaultUnselectAllHandler>
	 *
	 */ 
	this.unselectAll = function() {
		_unselectAllHandler();
	}
	
	/*
	 * Function: _defaultUnselectAllHandler
	 * Default handler provided for 'unselect All' operation
	 *
	 * See Also:
	 *
	 *  <setUnselectAllHandler>, <unselectAll>
	 *
	 */ 
	function _defaultUnselectAllHandler() {
		_toggleSelectAll(false);
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
		_unselectAllHandler = func ? func : _defaultUnselectAllHandler;
	}

	/*
	 * Function: _toggleSelectAll
	 * (Un)selects all table rows by checking checkboxes
	 *
	 * Parameters:
	 *
	 *  on - boolean: (de)selecting table's rows
	 *
	 */ 
	function _toggleSelectAll(on) {
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
	 * This function can be called many times by the <_executeQuery> function (iterative step).
	 *
	 * Parameters:
	 *
	 *  k - integer: index to determine row DOM node in table 
	 *  xhr - <HttpRequest> instance used to send query
	 *
	 * See Also:
	 *
	 * <_executeQuery>
	 *
	 */ 
	function sendq(k, xhr) {
		var row, rowNode, critText, valueText, params, rid;

		// Display field
		rowNode = topNode.childNodes[k];
		rid = rowNode.getAttribute('id');
		row = rid.substr(rid.search(/\d+$/));

		critNode = $(id + '_mainCriteria_select_' + row);
		condNode = $(id + '_condition_select_' + row);
		valueNode = $(id + '_custom_div_' + row).firstChild;

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
		var select = new Element('select', {'id': id + '_mainCriteria_select_' + tr_idx});
		// Call matching handler when selection changes
		select.observe('change', function() {
			_executeHandler(tr_idx);
		});

		var option;
		for (var j=0; j < fields.length; j++) {
			option = new Element('option');
			option.setAttribute('value', j);
			option.insert(labelFields[j]);
			select.insert(option);
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
	 * Function: _fileUploadStartHandler
	 * Executes start handler
	 *
	 */ 
	function _fileUploadStartHandler() {
		// make something useful before submit (onStart)
		var skydiv = $(id + '_sky_selections_div');
		var blog = $(id + '_batch_log_div');
		var log = $(id + '_upload_log_div');

		skydiv.innerHTML = '';
		$(id + '_batch_load_saved_log_div').innerHTML = '';

		if (blog) blog.style.display = 'none';
		log.innerHTML = '';
		log.innerHTML = getLoadingHTML('Uploading file...');

		return true;
	}

	/*
	 * Function: _fileUploadCompleteHandler
	 * Executes handler, wrapper for the public interface
	 *
	 * Parameters:
	 *
	 * resp - AJAX response
	 *
	 */ 
	function _fileUploadCompleteHandler(resp) {
		var r = eval('(' + resp + ')');
		var len = r['length'];
		var exit_code = r['exit_code'];
		var error_msg = r['error_msg'];
		var fileName = r['filename'];
	
		var log = $(id + '_upload_log_div');
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
			var img = new Element('img');
			img.setAttribute('src', '/media/themes/' + guistyle + '/img/admin/' + img_name);
			log.insert(img);
			// Dot not call Element#insert method to displaying HTML content
			log.appendChild(document.createTextNode(msg[k]));
			log.insert(new Element('br'));
		}
		if (exit_code) return;

		// View file content
		log.insert('(');
		var a = new Element('a');
		a.setAttribute('target', '_blank');
		a.setAttribute('href', '/youpi/uploadFile/batch/viewContent/' + fileName + '/');
		a.insert('View file content');
		log.insert(a);
		log.insert(')');

		var rdiv = new Element('div');
		rdiv.setAttribute('style', 'color: black;');
		rdiv.setAttribute('id', id + '_upload_content_div');
		log.insert(rdiv);

		var bdiv = $(id + '_batch_sel_div');
		var blog = new Element('div');
		blog.setAttribute('id', id + '_batch_log_div');
		blog.setAttribute('class', 'ims_batch_log_div');
		bdiv.insert(blog);

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
				var img = new Element('img');
				img.setAttribute('src', '/media/themes/' + guistyle + '/img/admin/' + img_name);
				rdiv.insert(img);
				rdiv.insert('Found ' + res['nbSelections'] + ' selection' + (res.nbSelections > 1 ? 's':''));

				var sel = res['selections'];
				var total = 0;
				// Reset batch selections
				_batchModeSelections.length = 0;

				for(var k=0; k<sel.length; k++) {
					var selbox = new DropdownBox(rdiv, 'View selection <b>' + (k+1) + '</b> - ' + sel[k].name + ', <i>' + 
						sel[k].count + ' images</i>');
					selbox.setTopLevelContainer(false);
					// Trick to pass custom data to the instance
					selbox.xml = encodeURI(sel[k]['xml']);
					selbox.xmlLoaded = false;
					selbox.setOnClickHandler(_handlerViewBatchSelection.bind(selbox));

					_batchModeSelections[k] = sel[k]['idList'];
					total += sel[k]['count'];
				}	
				rdiv.insert('<br/>Total: [ ' + total + ' images ]');

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
	 * Function: _handlerViewBatchSelection
	 * Dropdown box custom handler to view a batch selection
	 *
	 */ 
	function _handlerViewBatchSelection() {
		_viewBatchSelection(this.getContentNode(), this.xml);
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
		if (!$(id + '_batch_display_sky_check').checked) {
			if (!$(id + '_batch_sky_compute_all_check').checked)
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
			if ($(id + '_batch_sky_compute_all_check').checked)
				post += '&PlotCenter=1';
		}

		var skydiv = $(id + '_sky_selections_div');
		var xhr2 = new HttpRequest(
			skydiv.id,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				var a = new Element('a');
				a.setAttribute('href', resp['imgName']);
				a.setAttribute('target', '_blank');
				var img = new Element('img');
				img.setAttribute('src', resp['tnName']);
				skydiv.innerHTML = '';
				a.insert(img);
				skydiv.insert(a);
			}
		);

		// Send HTTP POST request
		xhr2.setBusyMsg('Loading sky visualization');
		xhr2.send('/youpi/plot/sky/selections/', post);
	}

	/*
	 * Function: _viewBatchSelection
	 * Display a selection's content into a new page
	 *
	 * Parameters:
	 *
	 * container - DOM container node
	 * xml - XML data selection
	 *
	 */ 
	function _viewBatchSelection(container, xml) {
		if (container.xmlLoaded) return;

		var xhr = new HttpRequest(
			container,
			// Use default error handler
			null,
			// Custom handler for results
			function(resp) {
				container.update();
				var pre = new Element('pre', {style: 'color: brown;'});
				pre.insert('Images in ' + resp['name'] + ' selection:<br/>');

				$A(resp.data).each(function(image) {
					pre.insert(image[0] + ' in ' + image[1] + '<br/>');
				});
				container.insert(pre);
				// Trick to prevent future AJAX queries for this DropdownBox instance
				container.xmlLoaded = true;
			}	
		);

		// Get all ids of images
		post = 'XML=' + xml;

		// Send HTTP POST request
		xhr.setBusyMsg('Retreiving selection content');
		xhr.send('/youpi/uploadFile/batch/viewSelection/', post);
	}

	/*
	 * Function: _main
	 * Entry point
	 *
	 */ 
	function _main() {
		_render();
		_setupSlots();
	}

	// Main entry point
	_main();
}
