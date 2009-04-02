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


if (!Youpi)
	var Youpi = {};

Youpi.GradingWidget = {};
Youpi.GradingWidget.currentId = 1;

/*
 * Class: GradingWidget
 * Simple widget displaying colored stars for grading purposes
 *
 * Note:
 *
 * Please note that this page documents Javascript code. <GradingWidget> is a pseudo-class, 
 * it provides encapsulation and basic public/private features.
 *
 * Constructor Parameters:
 *
 * container_id - string: name of parent DOM block container
 * startsCount - integer: number of stars to display
 *
 */
function GradingWidget(container_id, starsCount)
{
	var container = $(container_id);
	var id = 'gradw_' + Math.floor(Math.random() * 999999);
	Youpi.GradingWidget.currentId++;

	var starsCount = starsCount ? starsCount : 4;
	
	// Commit handler function
	var _commitHandler = _defaultCommitHandler;

	// Display legend caption
	var _legendEnabled = true;

	/*
	 * true: mouse events are captured. Grading is possible.
	 * false: no way to grade. Read-only widget.
	 *
	 */
	var _active = true;

	// No grade
	var E_NO_GRADE = -1;
	var currentGrade = E_NO_GRADE;
	var grades = new Array();
	var imgs = new Array();

	// Grade label div
	var gdiv = new Element('div');
	gdiv.setAttribute('class', 'result_panel_grade_label');
	var NO_GRADE = 'No grade';

	// Commit div
	var cdiv = new Element('div').hide();
	cdiv.setAttribute('id', id + '_commit');
	cdiv.setAttribute('class', 'result_panel_commit');

	/*
	 * Function: _draw
	 * Widget drawing
	 *
	 * Note:
	 * 
	 */
	function _draw() {
		var main = new Element('div');
		gdiv.appendChild(document.createTextNode(NO_GRADE));

		for (var k=0; k < starsCount; k++) {
			grades[k] = String.fromCharCode(65 + k);
			imgs[k] = new Element('img', {src: '/media/themes/' + guistyle + '/img/16x16/grading-star-off.gif'});
			if (_active) {
				imgs[k].writeAttribute('class', 'result_panel_star');
				imgs[k].sidx = k;
				imgs[k].observe('mouseover', function() {
					_enlight(this.sidx);
				});
				imgs[k].observe('click', function() {
					_setGrade(this.sidx);
				});
			}
			else {
				imgs[k].setStyle({cursor: 'default'});
			}
		}

		var sdiv = new Element('div');
		sdiv.setAttribute('style', 'text-align: center;');
		if (_active) {
			sdiv.observe('mouseout', function() {
				_deselectAll();
			});
		}
		for (var k=0; k < imgs.length; k++) {
			sdiv.appendChild(imgs[k]);
		}

		main.appendChild(gdiv);
		main.appendChild(sdiv);
		main.appendChild(cdiv);
		container.appendChild(main);
	}

	/*
	 * Function: setActive
	 * Sets wether the widget is active (responds to mouse events)
	 *
	 * Parameters:
	 *  on - boolean
	 *
	 * Note:
	 *  When inactive (off), mouse events are not captured. This widget becomes a read-only widget
	 * 
	 */
	this.setActive = function(on) {
		_active = typeof on == 'boolean' ? on : _active;	
		container.update();
		// Repaint widget
		_draw();
	}

	/*
	 * Function: isActive
	 * Returns wether the widget is active
	 *
	 * Returns:
	 *  on - boolean
	 * 
	 */
	this.isActive = function() {
		return _active;
	}

	/*
	 * Function: isGraded
	 * Returns wether a grade has been set
	 *
	 * Returns:
	 *  boolean
	 * 
	 */
	this.isGraded = function() {
		return currentGrade >=0;
	}

	/*
	 * Function: setLegendEnabled
	 * Sets wether the legend is displayed
	 *
	 * Parameters:
	 *  on - boolean
	 *
	 */
	this.setLegendEnabled = function (on) {
		_legendEnabled = on;
		_legendEnabled ? gdiv.show() : gdiv.hide();
	}

	/*
	 * Function: isLegendEnabled
	 * Returns wether the legend is displayed
	 *
	 * Returns:
	 *  on - boolean
	 *
	 */
	this.isLegendEnabled = function() {
		return _legendEnabled;
	}

	/*
	 * Function: deselectAll
	 * Remove grading
	 *
	 */
	this.deselectAll = function() {
		_deselectAll();
	}

	/*
	 * Function: _deselectAll
	 * Remove grading
	 *
	 */
	function _deselectAll() {
		if (currentGrade >= 0) {
			_enlight(currentGrade);
			return;
		}

		for (var k=0; k < imgs.length; k++) {
			imgs[k].writeAttribute('src', '/media/themes/' + guistyle + '/img/16x16/grading-star-off.gif');
		}
		gdiv.update(NO_GRADE);
	}

	/*
	 * Function: enlight
	 * Turn on stars
	 *
	 */
	this.enlight = function(idx) {
		_enlight(idx);
	}

	/*
	 * Function: _enlight
	 * Turn on stars
	 *
	 * Parameters:
	 *  idx - integer: index of grade
	 *
	 */
	function _enlight(idx) {
		for (var k=0; k <= idx; k++) {
			imgs[k].setAttribute('src', '/media/themes/' + guistyle + '/img/16x16/grading-star-on.gif');
		}
		for (var k=idx+1; k < imgs.length; k++) {
			imgs[k].setAttribute('src', '/media/themes/' + guistyle + '/img/16x16/grading-star-off.gif');
		}

		gdiv.innerHTML = '';
		gdiv.appendChild(document.createTextNode('Grade: ' + grades[starsCount-idx-1]));
	}

	/*
	 * Function: SetCharGrade
	 * Sets grade by char
	 *
	 * Parameters:
	 *  chr - string: single char grade (ranges from 'A' to 'Z')
	 *
	 */
	this.setCharGrade = function(chr) {
		if (typeof chr != 'string' || (typeof chr == 'string' && chr.length > 1))
			throw 'chr must be a single char string';

		var idx = starsCount - ((chr.charCodeAt(0) - 65 + starsCount) % starsCount) - 1;
		if (idx > starsCount || chr.length > 1)
			throw "Invalid grade '" + chr + "'.";

		currentGrade = idx;
		this.setGrade(idx);
	}

	/*
	 * Function: setGrade
	 * Sets grade by index
	 *
	 */
	this.setGrade = function(idx) {
		_setGrade(idx);
	}

	/*
	 * Function: _setGrade
	 * Sets grade by index
	 *
	 * Parameters:
	 *  idx - integer: index of grade (>=0)
	 *
	 */
	function _setGrade(idx) {
		if (idx < 0 || idx > grades.length-1) {
			currentGrade = E_NO_GRADE;
			return;
		}

		_enlight(idx);

		if (currentGrade != idx) {
			_showCommitButton();
		}

		currentGrade = idx;
	}

	/*
	 * Function: showCommitButton
	 * Display commit button
	 *
	 */
	this.showCommitButton = function() {
		_showCommitButton();
	}

	/*
	 * Function: _showCommitButton
	 * Display commit button
	 *
	 */
	function _showCommitButton() {
		cdiv.update();
		var cimg = new Element('img');
		cimg.setAttribute('src', '/media/themes/' + guistyle + '/img/misc/commit.gif');
		cimg.observe('click', function() {
			_commitHandler();
		});
		cdiv.insert(cimg);
		cdiv.show();
	}

	/*
	 * Function: getGrade
	 * Get current grade
	 *
	 * Returns:
	 *  char grade
	 *
	 */
	this.getGrade = function() {
		return grades[starsCount-currentGrade-1];
	}

	/*
	 * Function: getCommitDiv
	 * Get commit DIV node
	 *
	 * Returns:
	 *  DOM element
	 *
	 */
	this.getCommitDiv = function() {
		return cdiv;
	}

	/*
	 * Function: setCommitHandler
	 * Sets a custom handler function for committing action
	 *
	 * Parameters:
	 *  handler - function
	 *
	 */
	this.setCommitHandler = function(handler) {
		_commitHandler = handler ? handler : _defaultCommitHandler;
	}

	/*
	 * Function: getCommitHandler
	 * Returns current handler function for committing action
	 *
	 * Returns:
	 *  handler - function
	 *
	 */
	this.getCommitHandler = function() {
		return _commitHandler;
	}

	/*
	 * Function: _defaultCommitHandler
	 * Internal default commit handler function
	 *
	 * Returns:
	 *  true
	 *
	 */
	function _defaultCommitHandler() {
		// NOP handler
		cdiv.innerHTML = '';
		cdiv.appendChild(document.createTextNode('Committed, thanks !'));

		return true;
	}

	// Called when user clicks on 'commit' button
	this.commit = function() {
		// Executes handler
		_commitHandler();
	}

	_draw();
}
