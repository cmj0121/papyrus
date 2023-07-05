use criterion::{criterion_group, criterion_main, Criterion};
use papyrus::{Converter, Key, Value};

pub fn key_convert(c: &mut Criterion) {
    let int: i64 = 34182;
    let chr: &str = "Test Key";

    let int_bytes = Key::from(int).to_bytes();
    let chr_bytes = Key::from(chr).to_bytes();

    c.bench_function("int to Key", |b| b.iter(|| Key::from(int)));
    c.bench_function("chr to Key", |b| b.iter(|| Key::from(chr)));

    c.bench_function("int to Key Converter (to_bytes)", |b| {
        b.iter(|| Key::from(int).to_bytes())
    });
    c.bench_function("chr to Key Converter (to_bytes)", |b| {
        b.iter(|| Key::from(chr).to_bytes())
    });

    c.bench_function("int to Key Converter (from_bytes)", |b| {
        b.iter(|| Key::from_bytes(&int_bytes))
    });
    c.bench_function("chr to Key Converter (from_bytes)", |b| {
        b.iter(|| Key::from_bytes(&chr_bytes))
    });
}

pub fn value_convert(c: &mut Criterion) {
    let text: &str = "Test 測試 テスト prüfen ทดสอบ";
    let text_bytes = Value::from(text).to_bytes();

    c.bench_function("str to Value", |b| b.iter(|| Value::from(text)));

    c.bench_function("str to Value Converter (to_bytes)", |b| {
        b.iter(|| Value::from(text).to_bytes())
    });

    c.bench_function("str to Value Converter (from_bytes)", |b| {
        b.iter(|| Value::from_bytes(&text_bytes))
    });
}

criterion_group!(benches, key_convert, value_convert);
criterion_main!(benches);
