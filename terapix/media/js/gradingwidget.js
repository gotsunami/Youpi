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
 * varName - string: global variable name of instance, used internally for public interface definition
 * startsCount - integer: number of stars to display
 *
 */
function GradingWidget(container_id, varName, starsCount)
{
	// Name of instance if global namespace
	var instance_name = varName;
	var container = $(container_id);

	var id = varName + '_gradw_' + Youpi.GradingWidget.currentId;
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
			imgs[k] = new Element('img');
			imgs[k].setAttribute('src', '/media/themes/' + guistyle + '/img/16x16/grading-star-off.gif');
			if (_active) {
				imgs[k].setAttribute('class', 'result_panel_star');
				imgs[k].setAttribute('onmouseover', instance_name + ".enlight(" + k + ");");
				imgs[k].setAttribute('onclick', instance_name + ".setGrade(" + k + ");");
			}
			else {
				imgs[k].setAttribute('style', 'cursor: default;');
			}
		}

		var sdiv = new Element('div');
		sdiv.setAttribute('style', 'text-align: center;');
		if (_active) {
			sdiv.setAttribute('onmouseout', instance_name + ".deselectAll();");
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
		if (currentGrade >= 0) {
			this.enlight(currentGrade);
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
	 * Parameters:
	 *  idx - integer: index of grade
	 *
	 */
	this.enlight = function(idx) {
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
	 * Function: enlight
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
	 * Parameters:
	 *  idx - integer: index of grade (>=0)
	 *
	 */
	this.setGrade = function(idx) {
		if (idx < 0 || idx > grades.length-1) {
			currentGrade = E_NO_GRADE;
			return;
		}

		this.enlight(idx);

		if (currentGrade != idx) {
			this.showCommitButton();
		}

		currentGrade = idx;
	}

	/*
	 * Function: showCommitButton
	 * Display commit button
	 *
	 */
	this.showCommitButton = function() {
		cdiv.update();
		var cimg = new Element('img');
		cimg.setAttribute('src', '/media/themes/' + guistyle + '/img/misc/commit.gif');
		cimg.setAttribute('onclick', instance_name + '.commit()');
		cdiv.insert(cimg);
		cdiv.show();
		console.log(cimg);
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
