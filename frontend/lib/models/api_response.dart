class ApiResponse<T> {
  final bool success;
  final T? data;
  final String? error;

  ApiResponse({required this.success, this.data, this.error});

  factory ApiResponse.ok(T data) => ApiResponse(success: true, data: data);
  factory ApiResponse.fail(String error) =>
      ApiResponse(success: false, error: error);

  bool get isOk => success;
}

class PaginatedResponse<T> {
  final List<T> items;
  final int total;

  PaginatedResponse({required this.items, required this.total});

  factory PaginatedResponse.fromJson(
    Map<String, dynamic> json,
    T Function(Map<String, dynamic>) fromItem,
  ) {
    final list = (json['items'] as List<dynamic>?)
            ?.map((e) => fromItem(e as Map<String, dynamic>))
            .toList() ??
        [];
    return PaginatedResponse(
      items: list,
      total: json['total'] as int? ?? list.length,
    );
  }
}
