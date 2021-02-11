
/**
 * Checks to see if the user pressed cancel in chrome's file upload browser.
 * @param {String} filePath - A path to a file.
 * @returns {boolean} - True if the user selects cancel in chrome's file upload browser.
 */
function cancelWasPressedInChromeFileUpload(filePath) {
    return isEmptyStr(filePath) && (window.chrome)
}

/**
 * Checks to see if any entries in an array of names are empty.
 * @param {Array} names - An array containing a list of names.
 * @returns {boolean} - True if any of the names in the array are all empty.
 */
function columnNamesAreEmpty(names) {
    let numberOfNames = names.length;
    for (let i = 0; i < numberOfNames; i++) {
        if (!isEmptyStr(names[i].trim())) {
            return false;
        }
    }
    return true;
}

/**
 * Converts a path and prefix to a text results name
 * @param {String} filename - Pathname of the original file
 * @param {String} prefix - Prefix to be appended to the file name of original file
 * @returns {String} - File name of the
 */
function convertToResultsName(filename, prefix) {
    let parts = getFilenameAndExtension(filename);
    return prefix + "_" + parts[0] + ".txt"
}


/**
 * Compares the file extension of the file at the specified path to an Array of accepted file extensions.
 * @param {String} filePath - A path to a file.
 * @param {Array} acceptedFileExtensions - An array of accepted file extensions.
 * @returns {boolean} - True if the file has an accepted file extension.
 */
function fileHasValidExtension(filePath, acceptedFileExtensions) {
    let fileExtension = filePath.split('.').pop();
    if ($.inArray(fileExtension.toLowerCase(), acceptedFileExtensions) != -1) {
        return true;
    }
    return false;
}



/**
 * Flash a message on the screen.
 * @param {String} message - The message that will be flashed on the screen.
 * @param {String} category - The category of the message. The categories are 'error', 'success', and 'other'.
 * @param {String} flashMessageElementId - ID of the flash element
 */
function flashMessageOnScreen(message, category, flashMessageElementId) {
    let flashMessage = document.getElementById(flashMessageElementId);
    flashMessage.innerHTML = message;
    setFlashMessageCategory(flashMessage, category);
}


function getFilenameAndExtension(pathname){

  let clean = pathname.toString().replace(/^.*[\\\/]/, '');
  if (!clean) {
      return ['', '']
  }

  let filename = clean.substring(0, clean.lastIndexOf('.'));
  let ext = clean.split('.').pop();
  return [filename, ext];
}


/**
 * Gets the file download name from a Response header
 * @param {Object} xhr - Dictionary containing Response header information
 * @param {String} default_name - The default name to use
 * @returns {String} - Name of the save file
 */
function getFilenameFromResponseHeader(xhr, default_name) {
    let disposition = xhr.getResponseHeader('Content-Disposition')

    let filename = "";
    if (disposition && disposition.indexOf('attachment') !== -1) {
        let filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
        let matches = filenameRegex.exec(disposition);
        if (matches != null && matches[1]) {
            filename = matches[1].replace(/['"]/g, '');
        }
    }
    if (!filename) {
        filename = default_name;
    }
    return filename
}

/**
 * Gets standard failure response for download
 * @param {String} download - Downloaded string response blob
 * @param {Object} xhr - Dictionary containing Response header information
 * @param {String} display_name - Name used for the downloaded blob file
 * @param {String} flash_location - ID of the flash location element for displaying response Message
 */
function getResponseFailure(download, xhr, display_name, flash_location) {
    console.log(download.responseText);
    if (download.responseText.length < 100) {
        flashMessageOnScreen(download.responseText, 'error', flash_location);
    } else {
        flashMessageOnScreen('Not processed', 'error', flash_location);
    }
}

/**
 * Gets standard response with download
 * @param {String} download - Downloaded string response blob
 * @param {Object} xhr - Dictionary containing Response header information
 * @param {String} display_name - Name used for the downloaded blob file
 * @param {String} flash_location - ID of the flash location element for displaying response Message
 */
function getResponseSuccess(download, xhr, display_name, flash_location) {
    if (download) {
        let filename = getFilenameFromResponseHeader(xhr, display_name)
        triggerDownloadBlob(download, filename);
        let info = xhr.getResponseHeader('Message')
        let category =  xhr.getResponseHeader('Category')
        if (info) {
            flashMessageOnScreen(info, category, flash_location);
        } else {
            flashMessageOnScreen('', 'success', flash_location);
        }
    } else {
        flashMessageOnScreen('No errors found.', 'success', flash_location);
    }
}


/**
 * Checks to see if a string is empty. Empty meaning null or a length of zero.
 * @param {String} str - A string.
 * @returns {boolean} - True if the string is null or its length is 0.
 */
function isEmptyStr(str) {
    if (str === null || str.length === 0) {
        return true;
    }
    return false;
}


/**
 * Flash a message on the screen.
 * @param {Object} flashMessage - The li element containing the flash message.
 * @param {String} category - The category of the message. The categories are 'error', 'success', and 'other'.
 */
function setFlashMessageCategory(flashMessage, category) {
    if ("error" === category) {
        flashMessage.style.backgroundColor = 'lightcoral';
    } else if ("success" === category) {
        flashMessage.style.backgroundColor = 'palegreen';
    } else if ("warning" === category) {
        flashMessage.style.backgroundColor = 'orange';
    } else {
        flashMessage.style.backgroundColor = '#f0f0f5';
    }
}

/**
 * Trigger the "save as" dialog for a text blob to save as a file with display name.
 */
function triggerDownloadBlob(download_text_blob, display_name) {
    const url = window.URL.createObjectURL(new Blob([download_text_blob]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', display_name);
    document.body.appendChild(link);
    link.click();
}

/**
 * Updates a file label.
 * @param {String} filePath - The path to the dictionary.
 * @param {String} displayName - The ID of the label field to set
 */
function updateFileLabel(filePath, displayName) {
    let filename = filePath.split('\\').pop();
    $(displayName).text(filename);
}
