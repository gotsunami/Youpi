
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
	var container = document.getElementById(container_id);

	var id = varName + '_gradw_' + Youpi.GradingWidget.currentId;
	Youpi.GradingWidget.currentId++;

	var starsCount = starsCount ? starsCount : 4;
	
	// Commit handler function
	var commitHandler = defaultCommitHandler;

	// Legend caption
	var legendEnabled = true;

	/*
	 * true: mouse events are captured. Grading is possible.
	 * false: no way to grade. Read-only widget.
	 *
	 */
	var active = true;

	// No grade
	var E_NO_GRADE = -1;
	var currentGrade = E_NO_GRADE;
	var grades = new Array();
	var imgs = new Array();

	// Grade label div
	var gdiv = document.createElement('div');
	gdiv.setAttribute('class', 'result_panel_grade_label');
	var NO_GRADE = 'No grade';

	// Commit div
	var cdiv = document.createElement('div');
	cdiv.setAttribute('id', id + '_commit');
	cdiv.setAttribute('class', 'result_panel_commit');

	function draw() {
		var main = document.createElement('div');
		gdiv.appendChild(document.createTextNode(NO_GRADE));

		for (var k=0; k < starsCount; k++) {
			grades[k] = String.fromCharCode(65 + k);
			imgs[k] = document.createElement('img');
			imgs[k].setAttribute('src', '/media/themes/' + guistyle + '/img/16x16/grading-star-off.gif');
			if (active) {
				imgs[k].setAttribute('class', 'result_panel_star');
				imgs[k].setAttribute('onmouseover', instance_name + ".enlight(" + k + ");");
				imgs[k].setAttribute('onclick', instance_name + ".setGrade(" + k + ");");
			}
			else {
				imgs[k].setAttribute('style', 'cursor: default;');
			}
		}

		var sdiv = document.createElement('div');
		sdiv.setAttribute('style', 'text-align: center;');
		if (active) {
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

	// When inactive (off), mouse events are not captured. This widget becomes a 
	// read-only widget
	this.setActive = function(on) {
		active = on;		
		container.innerHTML = '';
		// Repaint widget
		draw();
	}

	this.isActive = function() {
		return active;
	}

	this.isGraded = function() {
		return currentGrade >=0;
	}

	this.setLegendEnabled = function (on){
		legendEnabled = on;
		var style = legendEnabled ? 'block' : 'none';
		gdiv.setAttribute('style', 'display: ' + style);
	}

	this.isLegendEnabled = function() {
		return legendEnabled;
	}

	this.deselectAll = function() {
		if (currentGrade >= 0) {
			this.enlight(currentGrade);
			return;
		}

		for (var k=0; k < imgs.length; k++) {
			imgs[k].setAttribute('src', '/media/themes/' + guistyle + '/img/16x16/grading-star-off.gif');
		}

		gdiv.innerHTML = '';
		gdiv.appendChild(document.createTextNode(NO_GRADE));
	}

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

	// chr: 'A' to 'Z'
	this.setCharGrade = function(chr) {
		var idx = starsCount - ((chr.charCodeAt(0) - 65 + starsCount) % starsCount) - 1;
		if (idx > starsCount || chr.length > 1) {
			alert("setCharGrade: invalide grade '" + chr + "'.");
			return;
		}

		currentGrade = idx;
		this.setGrade(idx);
	}

	// idx: int >= 0
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

	this.showCommitButton = function() {
		cdiv.style.display = 'block';
		cdiv.innerHTML = '';
		var cimg = document.createElement('img');
		cimg.setAttribute('src', '/media/themes/' + guistyle + '/img/misc/commit.gif');
		cimg.setAttribute('onclick', instance_name + '.commit()');
		cdiv.appendChild(cimg);
	}

	this.getGrade = function() {
		return grades[starsCount-currentGrade-1];
	}

	this.getCommitDiv = function() {
		return cdiv;
	}

	this.setCommitHandler = function(handler) {
		commitHandler = handler ? handler : defaultCommitHandler;
	}

	this.getCommitHandler = function() {
		return commitHandler;
	}

	function defaultCommitHandler() {
		// NOP handler
		cdiv.innerHTML = '';
		cdiv.appendChild(document.createTextNode('Committed, thanks !'));

		return true;
	}

	// Called when user clicks on 'commit' button
	this.commit = function() {
		// Executes handler
		commitHandler();
	}

	draw();
}
