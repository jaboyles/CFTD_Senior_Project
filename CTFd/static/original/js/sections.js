// Have a method to set the section number for the admin
function setSection(section) {
    $.ajax({
        method: "PUT",
        url: script_root + '/admin/section/' + section,
        success: function() {
            console.log("Section changed to " + section);
            getSection();
            location.reload();
        },
        error: function() {
            console.log("Section change failed");
        }
    });
}

function getSectionsCallback(sections) {
    for (var i = 0; i < sections.length; i++) {
        var sectionNumber = sections[i].sectionNumber;
        var dropdownItem = "<li onclick=setSection(" + sectionNumber + ")><a href='#'>" + sectionNumber + "</a></li>"
        $("#section-dropdown-menu").append(dropdownItem);
    }
}

function getSection() {
    $.ajax({
        method: "GET",
        url: script_root + '/admin/section',
        success: function(section) {
            console.log("You're in section " + section);
        },
        error: function() {
            console.log("Section get failed");
        }
    });
}

function getSections() {
    $.ajax({
        method: "GET",
        url: script_root + '/admin/sections',
        success: function(sectionData) {
            /*sectionString = "The sections are: ";
            for (i = 0; i < sectionData['sections'].length; i++) {
                sectionString += sectionData['sections'][i].sectionNumber + " ";
            }
            console.log(sectionString);*/
            getSectionsCallback(sectionData['sections']);
        },
        error: function() {
            console.log("Section listing failed");
        }
    });
}

$(document).ready(function() {
    if (admin == "True") {
        getSections();
    }
})