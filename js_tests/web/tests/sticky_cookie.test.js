QUnit.module("sticky_cookie");

QUnit.test("cookie", (assert) => {
  const done = assert.async(10);

  for (let i = 0; i < 5; i++) {
    fetch(
      "http://localhost:9000/cookie",
      { method: "GET", credentials: "include" },
    )
    .then((res) => {
      assert.true(res.ok);
    })
    .catch((err) => {
      throw err;
    })
    .finally(() => {
      done();
    });
  }
});
