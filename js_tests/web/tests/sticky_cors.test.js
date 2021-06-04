QUnit.module("sticky_cors");

QUnit.test("simple_request", (assert) => {
  const done = assert.async();

  fetch(
    "http://localhost:9000/cors/simple-request",
    { method: "GET" },
  )
  .then((res) => {
    assert.true(res.ok);
  })
  .catch((error) => {
    throw error;
  })
  .finally(() => {
    done();
  });
});

QUnit.test("preflight", (assert) => {
  const done = assert.async();
  const data = {
    account_id: "hogehoge",
    email_addr: "hogehoge@hoge.com",
    age: 99,
  };

  fetch(
    "http://localhost:9000/cors/preflight",
    {
      method: "POST",
      mode: "cors",
      body: JSON.stringify(data),
      headers: { "Content-Type": "application/json" },
    },
  )
  .then((res) => {
    assert.true(res.ok);
  })
  .catch((error) => {
    throw error;
  })
  .finally(() => {
    done();
  });
});
