var tablinks = document.getElementsByClassName("tab-links");
var tabcontents = document.getElementsByClassName("tab-contents");

function opentab(tabname) {
    for (tablink of tablinks) {
        tablink.classList.remove("active-link");
    }
    for (tabcontent of tabcontents) {
        tabcontent.classList.remove("active-tab");
    }
    event.currentTarget.classList.add("active-link");
    document.getElementById(tabname).classList.add("active-tab");
}


var sidemenu = document.getElementById("sidemenu");

function openmenu() {
    sidemenu.style.right = "0";
}
function closemenu() {
    sidemenu.style.right = "-200px";
}


const scriptURL = 'https://script.google.com/macros/s/AKfycbxdAKyEA36HA_p0k3KwMzMigxgFCZ1XegRBPfjgxlNaOK2CsOnP9hrEV_6V1ARCAJw3vw/exec'
const form = document.forms['submit-to-google-sheet']
const msg = document.getElementById("msg")

form.addEventListener('submit', e => {
    e.preventDefault()
    fetch(scriptURL, { method: 'POST', body: new FormData(form) })
        .then(response => {
            msg.innerHTML = "<span style='color: black;'>Message Sent Successfully!</span>";
            setTimeout(function () {
                msg.innerHTML = ""
            }, 5000)
            form.reset()
        })
        .catch(error => console.error('Error!', error.message))
})

const spinnerTexts = document.querySelectorAll('[class^="spinner__text--"]')
const texts = spinnerTexts[0].dataset.texts.split(',').map(text => text.trim());
const textPositions = [0, 1]

spinnerTexts.forEach((spinnerText, index) => {
    // Initialize the spinner texts' text
    spinnerText.innerText = texts[textPositions[index]]
    // Change text after every animation iteration
    spinnerText.addEventListener('animationiteration', e => {
        e.target.innerText = texts[++textPositions[index] % texts.length]
    })
})


document.addEventListener('DOMContentLoaded', function () {
    var cards = document.querySelectorAll('.card');

    for (var i = 0; i < cards.length; i++) {
        cards[i].addEventListener('click', function () {
            this.classList.toggle('card-flipped');
        });
    }
});
