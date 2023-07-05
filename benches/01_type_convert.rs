use criterion::{criterion_group, criterion_main, Criterion};
use papyrus::{Key, Value};

pub fn key_convert(c: &mut Criterion) {
    c.bench_function("int to Key", |b| b.iter(|| Key::from(34182)));
    c.bench_function("chr to Key", |b| b.iter(|| Key::from("Test Key")));
}

pub fn value_convert(c: &mut Criterion) {
    c.bench_function("str to Value", |b| {
        b.iter(|| Value::from("Test 測試 テスト prüfen ทดสอบ"))
    });
}

criterion_group!(benches, key_convert, value_convert);
criterion_main!(benches);
