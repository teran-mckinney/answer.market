# bitcoin-fiat: Convert Bitcoins to fiat with Javascript

Uses Coindesk's API which appears to not work with HTTPS: http://www.coindesk.com/api/

## Example

```
<script src="bitcoin-fiat.js"></script>
<form>
    <b>Satoshis:</b> <input id="satoshis" name="satoshis" type="number" value="100000" min="100000" max="100000000000" onchange="BitcoinFiat(this, 'usd');"><small> $<span id="usd">(Pending)</span>~ (USD) (How much you want to be paid.)</small><br/>
</form>
<script>
    /* Coax the element into being updated before a change. */
    document.getElementById('satoshis').onchange();
</script>
```

## License

[Unlicense](LICENSE)/Public domain
