/*
 * Asynchronous calls to proceed FITS tables
 *
 */

var ireq = null;
var timeoutId = null;
var finished = false;
var cancelled = false;
var data = new Object();
var r;

/*
 * Each call of this function processes one step ONLY.
 * A timer is responsible for calling this function as many times 
 * as needed to complete the whole thing.
 *   The use can cancel job processing at anytime by clicking the
 * 'Cancel' button.
 *
 * Also note that async calls are queued thus run in an ordered way.
 *
 */
function process_step() {
	if (!ireq) {
		ireq = createXMLHttpRequest();
	}
	else if (ireq.readyState != 0) {
		// Do nothing, wait for the current job to finish
		ireq.abort();
	}
	var percent;

	ireq.open('post', '/spica2/process/preingestion/run/', true);
	ireq.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');

	ireq.onreadystatechange = function() {
		if (ireq.readyState == 4) {
			if (ireq.status != 200) {
				r.innerHTML = 'Error: ' + ireq.responseText;
				return;
			}

			if (!cancelled) {
				r.innerHTML = 'Processing tables:';
				document.getElementById('status').style.display = 'block';
			}

			var res = ireq.responseText;
			data.currentPos++;

			percent = parseInt(data.currentPos*100/data.count);

			var cNode = document.getElementById('count');
			var tNode = document.getElementById('table');
			cNode.innerHTML = data.currentPos + '/' + data.count;
			tNode.innerHTML = '<tt>' + data.tables[data.currentPos-1] + '</tt>';

			myJsProgressBarHandler.setPercentage('process_bar', percent);

			if (!finished)
				timeoutId = setTimeout(process_step, 500);

			if (data.currentPos == data.count) {
				// All jobs are done
				clearTimeout(timeoutId);
				timeoutId = null;
				finished = true;
				myJsProgressBarHandler.setPercentage('process_bar', '100');

				var s = document.getElementById('submit_button');
				s.value = 'Run pre-ingestion';

				r.innerHTML = '';
				r.appendChild(document.createTextNode('All ' + data.count + ' jobs done.'));
			}
		}
	}

	// All args are POST data, not function arguments
	ireq.send("table=" + data.tables[data.currentPos] + "&path=" + data.path);
}

/*
 * This is the main entry point when user clicks on the 'Run pre-ingestion' button.
 *
 * process_preingestion() first issue an asynchronous call to the server to get 
 * related info on how much and what data to process (FITS tables). After that, it 
 * initiates the jobs processing.
 * 
 */
function process_preingestion() {
	var xreq = createXMLHttpRequest();

	finished = false;
	cancelled = false;

	if (!xreq) return;

	r = document.getElementById('running');

	// Handles progress bar
	myJsProgressBarHandler.setPercentage('process_bar', '0');

	xreq.open('post', '/spica2/process/preingestion/tablescount/', true);
	xreq.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');

	xreq.onreadystatechange = function() {
		if (xreq.readyState == 1) {
			r.innerHTML = getLoadingHTML('Preparing data to process');
			document.getElementById('status').style.display = 'none';
		}
		else if (xreq.readyState == 4) {
			if (xreq.status != 200) {
				r.innerHTML = 'Error: ' + xreq.responseText;
				return;
			}

			// Parses JSON response
			var res = eval(xreq.responseText);
			data.count = res[0]['tables'].length;
			data.tables = res[0]['tables'];
			data.path = res[0]['path'];
			data.currentPos = 0;

			var f = document.getElementById('form_preingestion');
			f.setAttribute('onsubmit', 'cancel_jobs(); return false');

			var b = document.getElementById('process_bar');
			b.style.display = 'block';

			var s = document.getElementById('submit_button');
			s.value = 'Interrupt';

			// Start processing
			process_step();
		}
	}

	/* Build and Send asynchronous POST HTTP query */
	var obj = document.getElementById('hid_input_path');
	xreq.send("path=" + obj.value)
}

function cancel_jobs()
{
	clearTimeout(timeoutId);
	timeoutId = null;
	finished = true;
	cancelled = true;

	f = document.getElementById('form_preingestion');
	f.setAttribute('onsubmit', 'process_preingestion(); return false');

	s = document.getElementById('submit_button');
	s.value = 'Start';

	r.innerHTML = '<div class="warning"><p>Interrupted by user !</p></div>';
}
	

