#!/bin/sh

set -e

fail() {
    echo FAIL: $*
    exit 1
}

flake8 wsgi.py

# Negative tests.

# Positive tests.

# Answer status tests.

for i in uncached cached; do
    echo Doing $i, more or less.
    curl -s localhost:8080/answer/1GZ9N1xbXp17K3kdmtPicxc6dhs4Cx97mN | grep -qF 'Answer:' || fail "1GZ9N1xbXp17K3kdmtPicxc6dhs4Cx97mN doesn't have answer unlocked."
    curl -s localhost:8080/answer/1PdDMhsUKzdk4KGThJ1yyh3kkAEaKnmLPu | grep -qF 'Answer:' || fail "1PdDMhsUKzdk4KGThJ1yyh3kkAEaKnmLPu doesn't have answer unlocked."
    curl -s localhost:8080/answer/12JXaCvoz4T7fXHtSfXQb31DXBeG3qNoeh | grep -qF 'To unlock the answer' || fail "Answer should be locked."
    curl -s localhost:8080/answer/16jZ8eePe3sVXNREJR9XHqgKku536816c8 | grep -qF 'To unlock the answer' || fail "Legacy answer should be locked."
    curl -s localhost:8080/answer/12Qp4Ec8TRz1RKwcRsBK7KSsngioQCn2B8 | grep -qF 'Answer: ' || fail "Pre coinfee legacy doesn't have answer unlocked."
    curl -s localhost:8080/answer/1CxeNFUnwLWL6PUkybnuAt9nsd8WX7oEkg | grep -qF 'Answer: ' || fail "Modern coinfee doesn't have answer unlocked."
    curl -s localhost:8080/answer/1PuyacMavgt1UiojYmE6dK7EtSQELgGm3h | grep -qF 'To unlock the answer' || fail "Modern coinfee answer should be locked."
    curl -s localhost:8080/answer/15iom2fDM5TbG9N2T4ESYrxZgsVSSoRUAQ | grep -qF '15iom2fDM5TbG9N2T4ESYrxZgsVSSoRUAQ' && fail "/transaction coinfee-era answer shows the same address when it should not."
    curl -s localhost:8080/answer/15iom2fDM5TbG9N2T4ESYrxZgsVSSoRUAQ | grep -qF '194ND5ENwjpqzcNUKsrzB2iD1tzxc2DiTh' || fail "coinfee address changed???"
    curl -s localhost:8080/answer/1PuyacMavgt1UiojYmE6dK7EtSQELgGm3h | grep -qF '1PuyacMavgt1UiojYmE6dK7EtSQELgGm3h' || fail "coinfee address changed for mostly modern coinfee /payment answer???"
    curl -s localhost:8080/answer/c0e56c55-dc0c-426b-809b | grep -qF 'Answer: ' || fail "Ultra modern coinfee answer should be unlocked."
    curl -s localhost:8080/answer/23a2e5c0-d456-4300-a419 | grep -qF 'To unlock the answer' || fail "Ultra modern coinfee answer should be locked."
done
