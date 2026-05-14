var PAPERS_PER_PAGE = 10;
var papersShown = 0;
var loadingMore = false;
var currentSort = "similarity";
var MONTH_ORDER = {"Jan":1,"Feb":2,"Mar":3,"Apr":4,"May":5,"Jun":6,"Jul":7,"Aug":8,"Sep":9,"Oct":10,"Nov":11,"Dec":12};
var SORT_LABELS = {"similarity": "Similarity", "newest": "Newest", "oldest": "Oldest", "citations": "Citations"};

$(window).bind("load", function () {
	results = null;
	currentTab = "papers";

	f = document.getElementById("query_field");
	f.style.height = "0px";
	f.style.height = f.scrollHeight + "px";

	// Making the textfield and placeholder act nice on iOS.
	$("#query_field").focus(function () {
		$("#query_field").addClass("placeholder_hidden");
	});

	$("#query_field").blur(function () {
		$("#query_field").removeClass("placeholder_hidden");
	});

	// Only autofocus the textfield if on desktop
	if (/Android|webOS|iPhone|iPad|iPod|BlackBerry/i.test(navigator.userAgent)) {
		$("#query_field").blur();
	} else {
		$("#query_field").focus();
	}

	// Expand textfield in accordance with text length
	$("#query_field").on("input", function () {
		this.style.height = 0;
		this.style.height = (this.scrollHeight) + "px";
	});

	// Handle toggling between papers and authors tabs
	$(".toggle").on("click", function () {
		if (this.dataset.tab == "papers") {
			togglePapersTab(true);
		} else {
			togglePeopleTab(true);
		}
	});

	// Toggle the right tab
	tabGetParameter = findGetParameter("tab");
	if (tabGetParameter != null) {
		if (tabGetParameter.toLowerCase() == "people") {
			currentTab = "people";
		} else {
			currentTab = "papers";
		}
	}

	// Insert query if present as GET parameter
	queryGetParameter = findGetParameter("q");
	if (queryGetParameter != null) {
		$("#query_field").val(queryGetParameter);
		$("#query_field").trigger("input"); // trigger resize
		performSearch();
	}

	// Listen for when user hits return
	$("#query_field").keypress(function (e) {
		if (e.which == 13) {
			performSearch();
			return false;
		}
	});

	// Sort dropdown toggle
	$("#sort_button").on("click", function (e) {
		e.stopPropagation();
		$("#sort_dropdown").toggle();
	});

	// Sort option selection
	$(".sort_option").on("click", function (e) {
		e.stopPropagation();
		let sort = this.dataset.sort;
		if (sort === currentSort) {
			$("#sort_dropdown").hide();
			return;
		}
		currentSort = sort;
		localStorage.setItem("sortPreference", sort);
		$(".sort_option").removeClass("sort_option_active");
		$(this).addClass("sort_option_active");
		$("#sort_label").text(SORT_LABELS[sort]);
		$("#sort_dropdown").hide();
		sortPapers();

		// Animate current cards out, then render new order in
		if ($("#results").hasClass("move_up")) {
			$("#results").removeClass("move_up");
			$("#results").one("transitionend", function () {
				addPapers(results["papers"]);
				$("#results").addClass("move_up");
			});
		} else {
			addPapers(results["papers"]);
			$("#results").addClass("move_up");
		}
	});

	// Native select sort (mobile)
	$("#sort_select").on("change", function () {
		let sort = $(this).val();
		if (sort === currentSort) return;
		currentSort = sort;
		localStorage.setItem("sortPreference", sort);
		$(".sort_option").removeClass("sort_option_active");
		$(`.sort_option[data-sort="${sort}"]`).addClass("sort_option_active");
		$("#sort_label").text(SORT_LABELS[sort]);
		sortPapers();

		if ($("#results").hasClass("move_up")) {
			$("#results").removeClass("move_up");
			$("#results").one("transitionend", function () {
				addPapers(results["papers"]);
				$("#results").addClass("move_up");
			});
		} else {
			addPapers(results["papers"]);
			$("#results").addClass("move_up");
		}
	});

	// Close sort dropdown when clicking outside
	$(document).on("click", function () {
		$("#sort_dropdown").hide();
	});
	$("#sort_container").on("click", function (e) {
		e.stopPropagation();
	});

	// Infinite scroll: load more papers when near bottom
	$(window).on("scroll", function () {
		if (currentTab !== "papers" || results == null) return;
		if (papersShown >= results["papers"].length) return;
		let scrollBottom = $(window).scrollTop() + $(window).height();
		let docHeight = $(document).height();
		if (docHeight - scrollBottom < 200) {
			showMorePapers();
		}
	});
});

function togglePapersTab(animated) {
	$('[data-tab="papers"]').first().addClass("toggle_enabled");
	$('[data-tab="people"]').first().removeClass("toggle_enabled");
	$("#sort_container").show();
	if (animated) {
		if ($("#results").hasClass("move_up")) {
			$("#results").removeClass("move_up");
			$("#results").one("transitionend", function () {
				addPapers(results["papers"]);
				$("#results").addClass("move_up");
			});
		} else {
			addPapers(results["papers"]);
			$("#results").addClass("move_up");
		}
	} else {
		addPapers(results["papers"]);
	}
	queryVal = findGetParameter("q");
	currentTab = "papers";
	updateGetParameter(queryVal, currentTab);
}

function togglePeopleTab(animated) {
	$('[data-tab="people"]').first().addClass("toggle_enabled");
	$('[data-tab="papers"]').first().removeClass("toggle_enabled");
	$("#sort_container").hide();
	if (animated) {
		if ($("#results").hasClass("move_up")) {
			$("#results").removeClass("move_up");
			$("#results").one("transitionend", function () {
				addAuthors(results["authors"]);
				$("#results").addClass("move_up");
			});
		} else {
			addAuthors(results["authors"]);
			$("#results").addClass("move_up");
		}
	} else {
		addAuthors(results["authors"]);
	}
	queryVal = findGetParameter("q");
	currentTab = "people";
	updateGetParameter(queryVal, currentTab);
}

function performSearch() {
	// Change textfield appearance
	field = document.getElementById("query_field");
	field.style.animationName = "change_color";
	field.readOnly = true;
	$(field).blur();

	let queryVal = $('textarea[name="query"]').val();

	// Submit request to backend
	$.getJSON("/search", {
		query: queryVal
	}, function (data) {
		console.log(data)
		field.style.animationName = "";
		field.readOnly = false;
		if (data["error"] == null) {
			results = data;
			resetSort();
			updateGetParameter(queryVal, currentTab);
			$("#error_container").hide();
			$("#tip").hide();
			if (data["citation_error"] != null) {
				$("#warning_text").text(data["citation_error"]);
				$("#warning_container").show();
				$('.sort_option[data-sort="citations"]').hide();
				$('#sort_select option[value="citations"]').remove();
				if (currentSort === "citations") {
					currentSort = "similarity";
					$(".sort_option").removeClass("sort_option_active");
					$('.sort_option[data-sort="similarity"]').addClass("sort_option_active");
					$("#sort_label").text(SORT_LABELS["similarity"]);
					$("#sort_select").val("similarity");
				}
			} else {
				$("#warning_container").hide();
				$('.sort_option[data-sort="citations"]').show();
				if ($('#sort_select option[value="citations"]').length === 0) {
					$('<option value="citations">Citations</option>').insertAfter('#sort_select option[value="similarity"]');
				}
			}
			if (currentTab == "people") {
				togglePeopleTab(true);
			} else {
				togglePapersTab(true);
			}
			/*$("#toggle_container").show();*/
			$("#toggle_container").addClass("appear");
		} else {
			$("#error_text").text(data["error"]);
			$("#error_container").show();
			$("#warning_container").hide();
		}
	});
}

function findGetParameter(parameterName) {
	var result = null;
	var tmp = [];
	location.search.substr(1).split("&").forEach(function (item) {
		tmp = item.split("=");
		if (tmp[0] === parameterName) {
			result = decodeURIComponent(tmp[1]);
		}
	});
	return result;
}

function updateGetParameter(query, tab) {
	protocol = window.location.protocol + "//";
	host = window.location.host;
	pathname = window.location.pathname;
	queryParam = `?q=${encodeURIComponent(query)}`
	tabParam = `&tab=${encodeURIComponent(tab)}`
	newUrl = protocol + host + pathname + queryParam + tabParam
	window.history.pushState({ path: newUrl }, '', newUrl);
}

function renderMath() {
	let config = [{ left: "$$", right: "$$", display: true },
	{ left: "$", right: "$", display: false }];
	renderMathInElement(document.body, { delimiters: config });
}

function resetSort() {
	let saved = localStorage.getItem("sortPreference");
	currentSort = saved && SORT_LABELS[saved] ? saved : "similarity";
	$(".sort_option").removeClass("sort_option_active");
	$(`.sort_option[data-sort="${currentSort}"]`).addClass("sort_option_active");
	$("#sort_label").text(SORT_LABELS[currentSort]);
	$("#sort_select").val(currentSort);
	$("#sort_dropdown").hide();
	if (currentSort !== "similarity") {
		sortPapers();
	}
}

function sortPapers() {
	if (results == null) return;
	let papers = results["papers"];
	if (currentSort === "similarity") {
		papers.sort((a, b) => b.score - a.score);
	} else if (currentSort === "newest") {
		papers.sort((a, b) => {
			if (b.year !== a.year) return b.year - a.year;
			return (MONTH_ORDER[b.month] || 0) - (MONTH_ORDER[a.month] || 0);
		});
	} else if (currentSort === "oldest") {
		papers.sort((a, b) => {
			if (a.year !== b.year) return a.year - b.year;
			return (MONTH_ORDER[a.month] || 0) - (MONTH_ORDER[b.month] || 0);
		});
	} else if (currentSort === "citations") {
		papers.sort((a, b) => {
			let ac = a.citation_count != null ? a.citation_count : -1;
			let bc = b.citation_count != null ? b.citation_count : -1;
			return bc - ac;
		});
	}
}

function resultClicked(e) {
	$(e).removeClass("result_clickable");
	$(e).find(".result_abstract").removeClass("truncated_text");
	$(e).find(".result_button_container").show();
}

function addPapers(data) {
	$("#results").empty();
	papersShown = 0;
	showMorePapers();
	$("#results").addClass("move_up");
}

function showMorePapers() {
	if (results == null || loadingMore) return;
	let papers = results["papers"];
	if (papersShown >= papers.length) return;

	loadingMore = true;
	let nextBatch = papers.slice(papersShown, papersShown + PAPERS_PER_PAGE);
	var html = "";
	nextBatch.forEach((e, i) => {
		html += addPaper(e, i);
	});
	$("#results").append(html);
	papersShown += nextBatch.length;
	renderMath();
	loadingMore = false;
}

function addPaper(result, index) {
	let dotClass = result.score >= 0.80 ? "dot_green" : "dot_orange";
	let citationHtml = "";
	if (result.citation_count != null) {
		let count = result.citation_count.toLocaleString();
		let label = result.citation_count === 1 ? "citation" : "citations";
		citationHtml = `<div class="result_citations" title="Citation count from Semantic Scholar"><p>${count} ${label}</p></div>`;
	}
	let delay = (index || 0) * 40;
	return `<div class="search_result result_clickable paper_appear" style="animation-delay: ${delay}ms" onclick="resultClicked(this)">
    <div class="result_top">
    <div class="result_year black"><p>${result.month} ${result.year}</p></div>
    <div class="result_top_right">
    ${citationHtml}
    <div class="result_score black" title="Cosine similarity">
        <p>${result.score}</p>
        <div class="result_dot ${dotClass}"></div>
    </div>
    </div>
    </div>
    <p class="result_title black">
    ${result.title}
    </p>
    <p class="result_authors">${result.authors}</p>
    <p class="result_abstract truncated_text black">${result.abstract}</p>
    <div class="result_button_container">
    <div class="result_button_flex">
        <a href="https://arxiv.org/abs/${result.id}" target="_blank">
        <div class="result_button">
            <div class="go_to_symbol"></div>
            <p>Go to Paper</p>
        </div>
        </a>
        <a href="/?q=${encodeURIComponent("https://arxiv.org/abs/" + result.id)}" target="_blank">
        <div class="result_button">
            <div class="similarity_symbol"></div>
            <p>Find Similar</p>
        </div>
        </a>
    </div>
    </div>
</div>`
}

function addAuthors(authors) {
	$("#results").empty();
	var html = '<div id="authors_flex">';
	authors.forEach(author => {
		html += addAuthor(author)
	})
	html += '</div>'
	$("#results").append(html);
	$("#results").addClass("move_up");
	renderMath();
}

function addAuthor(author) {
	let dotClass = author.avg_score >= 0.80 ? "dot_green" : "dot_orange";
	html = `<div class="author_container">
    <div class="author_top_row">
    <p class="author_name black">${author.author}</p>
    <div class="result_score black" title="Average cosine similarity">
        <p>${author.avg_score}</p>
        <div class="result_dot ${dotClass}"></div>
    </div>
    </div>
    <div class="num_papers_container">
    <div class="author_num_papers_info_symbol" data-author="${author.author}" onmouseover="infoHover(this)" onmouseout="infoLeave()"></div>
    <p class="author_num_papers black">${author.papers.length} matching papers</p>
    </div>
		<div class="info_container" data-author="${author.author}">
			<p class="black">Based on your query, we retrieved 100 papers. Of those, <b>${author.author}</b> was (co-) author on <b>${author.papers.length}</b>.</p>
		</div>`
	author.papers.forEach(paper => {
		html += `<a href="https://arxiv.org/abs/${paper.id}" class="author_paper" target="_blank">${paper.title}</a>`;
	});
	html += "</div>"
	return html
}

function infoHover(elem) {
	pos = $(elem).position();
	width = $(elem).width();
	height = $(elem).height();
	offsetLeft = $(elem).offset().left;
	infoAuthor = elem.dataset.author;
	$(".info_container").each(function(i, obj) {
		containerAuthor = obj.dataset.author;
		if (infoAuthor != containerAuthor) return
		centerX = pos.left + width / 2;
		bottomY = pos.top + height;
		containerWidth = $(obj).width();
		left = centerX-containerWidth/2;
		minLeftMargin = 10;
		if (left < minLeftMargin) {
			diff = minLeftMargin - left;
			$(obj).css({top: bottomY+10+"px", left: left+diff/2+"px", display: "block"});
		} else {
			$(obj).css({top: bottomY+10+"px", left: left+"px", display: "block"});
		}
	});
}

function infoLeave() {
	$(".info_container").each(function(i, obj) {
		$(obj).hide();
	});
}