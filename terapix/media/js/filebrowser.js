/*
 * Class: FileBrowser
 * Generic file browser widget (using treeview from TafelTree's GPL code)
 *
 * Note:
 *
 * Please note that this page documents Javascript code. <FileBrowser> is a pseudo-class, 
 * it provides encapsulation and basic public/private features.
 *
 * For convenience, private data member names (both variables and functions) start with an underscore.
 *
 * Constructor Parameters:
 *
 * container_id - string: name of parent DOM block container
 * varName - string: global variable name of instance, used internally for public interface definition
 *
 */
function FileBrowser(container_id, varName) {
	// Group: Constants
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Var: _instance_name
	 * Name of instance in global namespace
	 *
	 */
	var _instance_name = varName;
	/*
	 * Var: _MODES
	 * Selection modes available
	 *
	 * SINGLE or MULTI.
	 *
	 */
	var _MODES = { SINGLE: 0, MULTI: 1 };
	/*
	 * Var: _selectedPathTitle
	 * Selected Path title
	 *
	 */
	var _selectedPathTitle = 'Selected Paths';


	// Group: Variables
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Var: _selectedDataPaths
	 * Array of arrays of selected data paths
	 *
	 * Example:
	 *  _selectedDataPaths = [['path1', 20], ['path2', 100]]
	 *
	 */
	var _selectedDataPaths = new Array();
	/*
	 * Var: _treeviewHeight
	 * Holds treeview's height
	 *
	 * This is a string; it defaults to '300px'.
	 *
	 */
	var _treeviewHeight = '300px';
	/*
	 * Var: _selectionMode
	 * FileBrowser selection mode. See <_MODES>.
	 *
	 * Default value is SINGLE.
	 *
	 */
	var _selectionMode = _MODES.SINGLE;
	/*
	 * Var: _branchClickedHandler
	 * Callback function to handle branch click event
	 *
	 */
	var _branchClickedHandler = null;
	/*
	 * Var: _submitButtonHandler
	 * Callback function to handle submit button clicks
	 *
	 * Note:
	 *  Feature only available in multi selection mode.
	 *
	 */
	var _submitButtonHandler = null;
	/*
	 * Var: _tree
	 * TafelTree instance
	 *
	 * See Also:
	 * <http://tafel.developpez.com>
	 */
	var _tree = null;
	/*
	 * Var: _rootDataPath
	 * Path to root data
	 *
	 */
	var _rootDataPath = '/';
	/*
	 * Var: _rootTitle
	 * Root's (top-level node) title
	 *
	 */
	var _rootTitle = 'Root';
	/*
	 * Var: _headerTitle
	 * Widget's title (in the box's border)
	 *
	 */
	var _headerTitle = 'Path selector';
	/*
	 * Var: _filteringPatterns
	 * Array of patterns matching filenames
	 *
	 */
	var _filteringPatterns = ['*'];
	/*
	 * Var: _root
	 * JSON element describing tree's root
	 *
	 */
	var _root;
	/*
	 * Var: _isRendered
	 * true if widget already rendered; false if not.
	 *
	 * See Also:
	 *  <render>
	 */
	var _isRendered = false;


	// Group: Functions
	// -----------------------------------------------------------------------------------------------------------------------------


	/*
	 * Function: setSelectionMode
	 * Sets current selection mode
	 *
	 * Use:
	 *  setSelectionMode(getSelectionModes().SINGLE)
	 *
	 * Parameters:
	 *
	 * mode - int: selection mode
	 *
	 */ 
	this.setSelectionMode = function(mode) {
		if (mode != _MODES.SINGLE && mode != _MODES.MULTI) {
			console.error("Unknown selection mode '" + mode + "'");
			_selectionMode = _MODES.SINGLE;
			return;
		}

		_selectionMode = mode;
		if (_isRendered) _renderSelectionMode();
	}

	/*
	 * Function: getSelectionModes
	 * Gets available selection modes
	 *
	 * Use:
	 *
	 * this.getSelectionModes().{SINGLE,MULTI}
	 *
	 * Returns:
	 *
	 * JSON object
	 *
	 */ 
	this.getSelectionModes = function() {
		return _MODES;
	}

	/*
	 * Function: setBranchClickedHandler
	 * Defines custom function handler to use when a treeview's branch is clicked
	 *
	 * Parameters:
	 *
	 *  handler - callback function 
	 *
	 */ 
	this.setBranchClickedHandler = function(handler) {
		_branchClickedHandler = handler ? handler : null;
	}

	/*
	 * Function: getBranchClickedHandler
	 * Gets custom function handler to use when a treeview's branch is clicked
	 *
	 * Returns:
	 *
	 *  Callback function handler
	 *
	 */ 
	this.getBranchClickedHandler = function() {
		return _branchClickedHandler;
	}

	/*
	 * Function: setSubmitButtonHandler
	 * Defines custom function handler to use when submit button is clicked
	 *
	 * Parameters:
	 *
	 *  handler - callback function 
	 *
	 * Note:
	 *  Has no effect in SINGLE selection mode.
	 *
	 */ 
	this.setSubmitButtonHandler = function(handler) {
		_submitButtonHandler = handler ? handler : null;
	}

	/*
	 * Function: getSubmitButtonHandler
	 * Gets custom function handler to use when submit button is clicked
	 *
	 * Returns:
	 *
	 *  Callback function handler
	 *
	 */ 
	this.getSubmitButtonHandler = function() {
		return _submitButtonHandler;
	}

	/*
	 * Function: setRootDataPath
	 * Defines base path to data
	 *
	 * Parameters:
	 *
	 *  path - string: path to data
	 *
	 */ 
	this.setRootDataPath = function(path) {
		_rootDataPath = path;
	}

	/*
	 * Function: getRootDataPath
	 * Gets base path to data
	 *
	 * Returns:
	 *
	 *  String path to data
	 *
	 */ 
	this.getRootDataPath = function() { 
		return _rootDataPath; 
	}

	/*
	 * Function: getSelectedDataPaths
	 * Gets base path to data
	 *
	 * Returns:
	 *
	 *  Array of arrays of selected data paths.
	 *
	 * Example:
	 *  return [['path1', 20], ['path2', 100]]
	 *
	 */ 
	this.getSelectedDataPaths = function() { 
		return _selectedDataPaths; 
	}

	/*
	 * Function: setRootTitle
	 * Defines root's (top-level node) caption
	 *
	 * Parameters:
	 *
	 *  name - string: root's title
	 *
	 */ 
	this.setRootTitle = function(name) {
		_rootTitle = name;
	}

	/*
	 * Function: getRootTitle
	 * Gets root's (top-level node) caption
	 *
	 * Returns:
	 *
	 *  Root's title
	 *
	 */ 
	this.getRootTitle = function() { 
		return _rootTitle; 
	}

	/*
	 * Function: setHeaderTitle
	 * Defines header title located in widget's border
	 *
	 * Parameters:
	 *
	 *  name - string: header title
	 *
	 */ 
	this.setHeaderTitle = function(name) {
		_headerTitle = name;
	}

	/*
	 * Function: getHeaderTitle
	 * Gets header title located in widget's border
	 *
	 * Returns:
	 *
	 *  Header title
	 *
	 */ 
	this.getheaderTitle = function() { 
		return _headerTitle; 
	}

	/*
	 * Function: setFilteringPatterns
	 * Defines string patterns used to filter names in directories
	 *
	 * Parameters:
	 *
	 *  patternList - array: filename patterns
	 *
	 */ 
	this.setFilteringPatterns = function(patternList) {
		_filteringPatterns = patternList;
	}

	/*
	 * Function: getFilteringPatterns
	 * Gets string patterns used to filter names in directories
	 *
	 * Returns:
	 *
	 *  Filename patterns
	 *
	 */ 
	this.getFilteringPatterns = function() { 
		return _filteringPatterns; 
	}

	/*
	 * Function: render
	 * Renders widget
	 *
	 * See Also:
	 *
	 * <_renderBase>, <_renderSelectionMode>
	 *
	 */ 
	this.render = function() {
		_renderBase();
		// per-mode rendering
		_renderSelectionMode();

		_isRendered = true;
	}

	/*
	 * Function: _renderBase
	 * Renders base widget
	 *
	 */ 
	function _renderBase() {
		var tr, th, td;
		var tab = document.createElement('table');
		tab.setAttribute('id', container_id + '_fb_tab');
		tab.setAttribute('class', 'fileBrowser');
		var container = document.getElementById(container_id);
		container.appendChild(tab);

		tr = document.createElement('tr');
		th = document.createElement('th');
		th.appendChild(document.createTextNode(_headerTitle));
		tr.appendChild(th);
		tab.appendChild(tr);

		tr = document.createElement('tr');
		td = document.createElement('td');
		td.setAttribute('id', container_id + '_tree');
		tr.appendChild(td);
		tab.appendChild(tr);

		// Selected paths (in MULTI selection mode)
		if (_selectionMode == _MODES.MULTI) {
			tr = document.createElement('tr');
			th = document.createElement('th');
			th.setAttribute('id', container_id + '_sel_path_th');
			th.appendChild(document.createTextNode(_selectedPathTitle));
			tr.appendChild(th);
			tab.appendChild(tr);
	
			tr = document.createElement('tr');
			tr.setAttribute('id', container_id + '_sel_mode_tr');
			td = document.createElement('td');
			td.setAttribute('style', 'width: 320px; margin: 0px; padding: 0px;');
	
			var d = document.createElement('div');
			d.setAttribute('id', container_id + '_sel_mode_div');
			d.setAttribute('style', 'overflow: auto; height: 80px; vertical-align: center;'); 
			td.setAttribute('id', container_id + '_tree');
			td.appendChild(d);
			tr.appendChild(td);
			tab.appendChild(tr);
		}

		// root's JSON branch
		_root = [ {
			'id'				: 'root',
			'txt'				: _rootTitle,
			'img'				: 'base.gif',
			'imgopen'			: 'base.gif',
			'imgclose'			: 'base.gif',
			'canhavechildren'	: true,
	//		'tooltip'			: '<h3>Test</h3>',
			'onopenpopulate' 	: _resultHandler,
			/*
			 * Server-side URL: /youpi/populate/file_pattern/_instance_name/path/to/data/
			 *
			 */
			'openlink'			: '/youpi/populate_generic/' + _filteringPatterns + '/' + _instance_name + '/' + _rootDataPath + '/'
		} ];

		if (_tree) delete _tree;
		_tree = new TafelTree(container_id + '_tree', _root, {
			'generate'			: true,
			'imgBase'			: '/media/js/3rdParty/tafelTree/imgs/',
			'height'			: _treeviewHeight,
			'defaultImg'		: 'page.gif',
			'defaultImgOpen'	: 'folderopen.gif',
			'defaultImgClose'	: 'folder.gif',
			'onClick'			: _branchClicked,
			'cookies'			: false } 
		);
	}

	/*
	 * Function: _getNoSelectionElement
	 * Returns a div element for 'No selection'
	 *
	 * Returns:
	 *  DOM div element
	 *
	 */ 
	function _getNoSelectionElement() {
		var div = document.createElement('div');
		div.setAttribute('style', 'width: 310px; padding-top: 30px; color: lightgray; text-align: center; vertical-align: center; font-size: 20px;');
		div.appendChild(document.createTextNode('No selection'));
		return div;
	}

	/*
	 * Function: _renderSelectionMode
	 * Renders mode part only
	 *
	 */ 
	function _renderSelectionMode() {
		var tr = document.getElementById(container_id + '_sel_mode_tr');
		if (_selectionMode == _MODES.SINGLE) {
			return;
		}

		tr.style.display = 'block';
		tr.firstChild.style.width = '*';
		var d = document.getElementById(container_id + '_sel_mode_div');
		
		var tab = document.createElement('table');
		tab.setAttribute('class', 'selModeMulti');
		var td;
		var tr = document.createElement('tr');
		td = document.createElement('td');
		td.appendChild(_getNoSelectionElement());
		tr.appendChild(td);
		td = document.createElement('td');
		tr.appendChild(td);
		tab.appendChild(tr);
		d.appendChild(tab);

		var but = document.createElement('input');
		but.setAttribute('type', 'button');
		but.setAttribute('value', 'Run ingestions');
		but.setAttribute('onclick', _instance_name + ".submitButtonClicked();");

		var cbut = document.createElement('input');
		cbut.setAttribute('style', 'margin-right: 10px;');
		cbut.setAttribute('type', 'button');
		cbut.setAttribute('value', 'Clear selection');
		cbut.setAttribute('onclick', _instance_name + ".clearAllSelections();");

		var d = document.createElement('div');
		d.setAttribute('id', _instance_name + '_submit_div');
		d.setAttribute('style', 'text-align: right; padding-right: 10px; display: none;');
		d.appendChild(cbut);
		d.appendChild(but);

		var n = tab.parentNode.parentNode;
		n.appendChild(d);
	}

	/*
	 * Function: submitButtonClicked
	 * Process data in MULTI selection mode by calling custom handler
	 *
	 * See Also:
	 *  <setSubmitButtonHandler>, <getSubmitButtonHandler>, <_submitButtonHandler>
	 *
	 */ 
	this.submitButtonClicked = function() {
		if (!_submitButtonHandler) {
			alert('No custom submit button handler defined!')
			return;
		}

		// Call custom handler
		_submitButtonHandler();
	}

	/*
	 * Function: setTreeviewHeight
	 * Sets treeview's height
	 *
	 * Arguments:
	 *  height - string: treeview's height (default is '300px')
	 *
	 */ 
	this.setTreeviewHeight = function(height) {
		_treeviewHeight = height;	
	}

	/*
	 * Function: getTreeviewHeight
	 * Gets treeview's height
	 *
	 * Returns:
	 *  treeview's height (default is '300px')
	 *
	 */ 
	this.getTreeviewHeight = function() {
		return _treeviewHeight;
	}

	/*
	 * Function: getResultHandler
	 * Returns TafelTree's result handler
	 *
	 * Returns:
	 *
	 *  Callback result handler when a leaf is to be populated
	 *
	 */ 
	this.getResultHandler = function() { return _resultHandler; }

	/*
	 * Function: _resultHandler
	 * Default result handler used by TafelTree <_tree> instance
	 *
	 * Returns:
	 *
	 *  Response
	 *
	 */ 
	function _resultHandler(branch, response) {
		// Tree is populated when AJAX response is returned
		return response;
	}

	/*
	 * Function: _branchClicked
	 * Calls custom handler function when a branch is clicked
	 *
	 * Parameters:
	 *
	 *  branch - current branch object
	 *
	 */ 
	function _branchClicked(branch) {
		var id = branch.getId();
		var nb = branch.struct.num_children;
		var dataPath = branch.struct.syspath;

		if (!_branchClickedHandler && _selectionMode == _MODES.SINGLE) {
			alert("FileBrower '" + _instance_name + "': no branchClicked handler defined!");
			return;
		}

		// Call custom handler
		if (_branchClickedHandler) 
			_branchClickedHandler(branch);
		
		if (_selectionMode != _MODES.MULTI)
			return;

		if (id == 'root' || !branch.hasChildren() || nb == 0)
			return;

		var d = document.getElementById(container_id + '_sel_mode_div');
		var tab = d.firstChild;

		if (_selectedDataPaths.length == 0 && tab.childNodes.length)
			tab.removeChild(tab.firstChild);

		// Path already clicked and added?
		for (var k=0; k < _selectedDataPaths.length; k++) {
			if (dataPath == _selectedDataPaths[k][0])
				return;
		}
		_selectedDataPaths[_selectedDataPaths.length] = [dataPath, nb];

		// Add new row
		var tr, td;
		// Delete action
		tr = document.createElement('tr');
		var trid =  container_id + '_added_path_tr_' + (_selectedDataPaths.length-1);
		tr.setAttribute('id', trid);

		td = document.createElement('td');
		var img = document.createElement('img');
		img.setAttribute('style', 'cursor: pointer; vertical-align: middle;');
		img.setAttribute('src', '/media/themes/' + guistyle + '/img/16x16/cancel.png');
		img.setAttribute('onclick', _instance_name + ".removeDataPath(" + (_selectedDataPaths.length-1) + ");");
		td.appendChild(img);
		tr.appendChild(td);

		// Images count
		td = document.createElement('td');
		td.setAttribute('class', 'imgCount');
		td.appendChild(document.createTextNode(nb));
		tr.appendChild(td);
		tab.appendChild(tr);

		// Data path
		td = document.createElement('td');
		td.setAttribute('class', 'path');
		td.appendChild(document.createTextNode(dataPath));
		tr.appendChild(td);
		tab.appendChild(tr);

		// Updates header title
		_updateSelectedPathsHeaderTitle();
	}

	/*
	 * Function: _updateSubmitButtonArea
	 * Show/Hide submit button area
	 *
	 */ 
	function _updateSubmitButtonArea() {
		// Run ingestion button
		var d = document.getElementById(_instance_name + '_submit_div');
		var style;
		_selectedDataPaths.length > 0 ? style = 'block' : style = 'none';
		d.style.display = style;
	}

	/*
	 * Function: _updateSelectedPathsHeaderTitle
	 * Updates header title when selected paths change
	 *
	 */ 
	function _updateSelectedPathsHeaderTitle() {
		var th = document.getElementById(container_id + '_sel_path_th');
		var total = 0;
		for (var k=0; k < _selectedDataPaths.length; k++) {
			total += _selectedDataPaths[k][1];
		}
		th.innerHTML = _selectedPathTitle + (total > 0 ? ': ' + _selectedDataPaths.length + ' (' + total + ' images)' : '');

		_updateSubmitButtonArea();
	}

	/*
	 * Function: clearAllSelections
	 * Clears all current selections
	 *
	 */ 
	this.clearAllSelections = function() {
		var count = _selectedDataPaths.length;
		for (var k=0; k < count; k++) {
			alert(k);
			this.removeDataPath(k);
		}
	}

	/*
	 * Function: removeDataPath
	 * Removes a data path from the list
	 *
	 * Parameters:
	 *	num - int: table row index (starts from 0)
	 *
	 */ 
	this.removeDataPath = function(num) {
		var trid = container_id + '_added_path_tr_' + num;
		var tr =  document.getElementById(trid);
		var tab = tr.parentNode;

		var pos = 0;
		var c = tab.firstChild;
		while (c = c.nextSibling) {
			if (c.getAttribute('id') == trid)
				break;
			pos++;
		}

		var a = new Array();
		var i = 0;
		for (var k=0; k < _selectedDataPaths.length; k++) {
			if (k != pos)
				a[i++] = _selectedDataPaths[k];
		}
		_selectedDataPaths = a;
		tab.removeChild(tr);

		if (_selectedDataPaths.length == 0) {
			tr = document.createElement('tr');
			td = document.createElement('td');
			td.appendChild(_getNoSelectionElement());
			tr.appendChild(td);
			tab.appendChild(tr);
		}

		// Updates header title
		_updateSelectedPathsHeaderTitle();
	}
}
