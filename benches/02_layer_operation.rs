use criterion::{criterion_group, criterion_main, Criterion};
use papyrus::{get_layer, Key, Value};

fn bench_layer_operation(c: &mut Criterion, url: &str) {
    let keys: Vec<Key> = (0..1000).map(|i| Key::from(i)).collect();
    let value: Value = "hello world".into();

    c.bench_with_input(criterion::BenchmarkId::new("put", url), &url, |b, url| {
        let mut layer = get_layer(url).unwrap();

        b.iter(|| {
            keys.iter().for_each(|key| {
                let _ = layer.put(key, value.clone());
            });
        });

        layer.unlink();
    });

    c.bench_with_input(criterion::BenchmarkId::new("iter", url), &url, |b, url| {
        let mut layer = get_layer(url).unwrap();

        keys.iter().for_each(|key| {
            let _ = layer.put(key, value.clone());
        });

        b.iter(|| {
            let _ = layer.iter().collect::<Vec<_>>();
        });

        layer.unlink();
    });

    c.bench_with_input(
        criterion::BenchmarkId::new("forward", url),
        &url,
        |b, url| {
            let mut layer = get_layer(url).unwrap();

            keys.iter().for_each(|key| {
                let _ = layer.put(key, value.clone());
            });

            b.iter(|| {
                let _ = layer.forward(None).collect::<Vec<_>>();
            });

            layer.unlink();
        },
    );

    c.bench_with_input(
        criterion::BenchmarkId::new("backward", url),
        &url,
        |b, url| {
            let mut layer = get_layer(url).unwrap();

            keys.iter().for_each(|key| {
                let _ = layer.put(key, value.clone());
            });

            b.iter(|| {
                let _ = layer.backward(None).collect::<Vec<_>>();
            });

            layer.unlink();
        },
    );
}

pub fn layer_operation(c: &mut Criterion) {
    bench_layer_operation(c, "mem://");
    bench_layer_operation(c, "wal://bench_wal");
}

criterion_group!(benches, layer_operation);
criterion_main!(benches);
