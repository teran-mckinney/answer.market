/*    bitcoin-fiat.js by Teran McKinney    */
/*    Released into the public domain.     */
/*          http://go-beyond.org/          */
/* https://github.com/coinfee/bitcoin-fiat */

var rate = false;

/* input: this */
/* ouput: ID of element that you want to receive the result. */
function BitcoinFiat(input, output) {
    function updateElement() {
        var element = document.getElementById(output);
        element.innerHTML = (rate * input.value * 0.00000001).toFixed(2);
    }
    /* This is a little awkward due to using XMLHTTPRequest asyncronously. We want to "cache" the result, too. */
    if (rate === false) {
        var request = new XMLHttpRequest();
        request.open("get", "http://api.coindesk.com/v1/bpi/currentprice/USD.json", true);
        request.responseType = "json";
        request.onload = function() {
            rate = request.response.bpi.USD.rate_float
            updateElement();
        };
        request.send();
    } else {
       updateElement();
    }
}
