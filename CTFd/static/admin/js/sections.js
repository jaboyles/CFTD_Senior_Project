// Have a method to set the section number for the admin
function setSection(section){
    $.ajax({
        method: "PUT",
        url: script_root + '/admin/section/' + section,
        success: function() {
            console.log("Section changed to " + section);
            getSection();
        },
        error: function() {
            console.log("Section change failed");
        }
    });
}

function getSection(){
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

function getSections(){
    $.ajax({
        method: "GET",
        url: script_root + '/admin/sections',
        success: function(sectionData) {
            sectionString = "The sections are: ";
            for (i = 0; i < sectionData['sections'].length; i++) {
                sectionString += sectionData['sections'][i].sectionNumber + " ";
            }
            console.log(sectionString);
        },
        error: function() {
            console.log("Section listing failed");
        }
    });
}

$(document).ready(function() {
    setSection(2);
    getSections();
})