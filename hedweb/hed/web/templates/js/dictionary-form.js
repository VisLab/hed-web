
$(function () {
    prepareForm();
});

/**
 * Submits the form if the tag columns textbox is valid.
 */
$('#dictionary-validation-submit').on('click', function () {
    if (fileIsSpecified('#json-file', 'json-flash', 'JSON is not specified.' ) && hedSpecifiedWhenOtherIsSelected()) {
        submitForm();
    }
});

/**
 * Clear the fields in the form.
 */
function clearForm() {
    $('#dictionary-form')[0].reset();
    clearFormFlashMessages()
    clearJsonFileLabel();
    hideOtherHEDVersionFileUpload()
}

/**
 * Clear the flash messages that aren't related to the form submission.
 */
function clearFormFlashMessages() {
    clearJsonInputFlashMessages();
    clearHedSelectFlashMessages();
    flashMessageOnScreen('', 'success', 'dictionary-validation-submit-flash');
}

/**
 * Prepare the validation form after the page is ready. The form will be reset to handle page refresh and
 * components will be hidden and populated.
 */
function prepareForm() {
    clearForm();
    getHedVersions()
    hideOtherHEDVersionFileUpload();
}

/**
 * Submit the form and return the validation results. If there are issues then they are returned in an attachment
 * file.
 */
function submitForm() {
    let dictionaryForm = document.getElementById("dictionary-form");
    let formData = new FormData(dictionaryForm);

    let dictionaryFile = getJsonFileLabel();
    let display_name = convertToResultsName(dictionaryFile, 'issues')
    clearFormFlashMessages();
    flashMessageOnScreen('Dictionary is being validated ...', 'success', 'dictionary-validation-submit-flash')
    $.ajax({
            type: 'POST',
            url: "{{url_for('route_blueprint.get_dictionary_validation_results')}}",
            data: formData,
            contentType: false,
            processData: false,
            dataType: 'text',
            success: function (download, status, xhr) {
                getResponseSuccess(download, xhr, display_name, 'dictionary-validation-submit-flash')
            },
            error: function (download, status, xhr) {
                getResponseFailure(download, xhr, display_name, 'dictionary-validation-submit-flash')
            }
        }
    )
}
