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
 * Class: LightFileBrowser
 * Generic file browser widget (using treeview from TafelTree's GPL code)
 *
 * Note:
 *  For convenience, private data member names (both variables and functions) start with an underscore.
 *
 * Constructor Parameters:
 *  varName - string: global variable name of instance, used internally for public interface definition
 *
 */
function LightFileBrowser(varName) {
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


	var _container;
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
		if (_container) _updateTreeRoot();
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
	 * <_renderBase>
	 *
	 */ 
	this.render = function() {
		var c =_renderBase();
		_isRendered = true;
		return c;
	}

	/*
	 * Function: _renderBase
	 * Renders base widget
	 *
	 */ 
	function _renderBase() {
		_container = new Element('div').addClassName('home');
		_updateTreeRoot();
		return _container;
	}
	
	function _updateTreeRoot() {
		if (_container) _container.update();
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
		_tree = new TafelTree(_container, _root, {
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
		var dataPath = id != 'root' ? branch.struct.syspath : null;

		if (!_branchClickedHandler)
			throw("FileBrower '" + _instance_name + "': no branchClicked handler defined!");

		// Call custom handler
		if (_branchClickedHandler) 
			_branchClickedHandler(dataPath);
		
		if (id == 'root' || !branch.hasChildren() || nb == 0)
			return;
	}
}
