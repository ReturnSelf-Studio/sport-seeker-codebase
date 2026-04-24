import 'dart:io';
import 'package:flutter/material.dart';
import '../../theme.dart';

class SearchResultsWidget extends StatelessWidget {
  final bool isSearching;
  final List<dynamic> results;
  final Function(String) onOpenFile;

  const SearchResultsWidget({
    super.key,
    required this.isSearching,
    required this.results,
    required this.onOpenFile,
  });

  @override
  Widget build(BuildContext context) {
    if (isSearching) return const Center(child: CircularProgressIndicator());
    if (results.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.image_not_supported_outlined, size: 64, color: AppTheme.textSecondary.withOpacity(0.5)),
            const SizedBox(height: 16),
            const Text('Không tìm thấy hình ảnh/video tương ứng.',
                style: TextStyle(color: AppTheme.textPrimary, fontSize: 16, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            const Text('Có thể người này không xuất hiện, hoặc dự án chưa được cấu hình xử lý.',
                style: TextStyle(color: AppTheme.textSecondary, fontSize: 13)),
          ],
        ),
      );
    }

    return GridView.builder(
      gridDelegate: const SliverGridDelegateWithMaxCrossAxisExtent(
          maxCrossAxisExtent: 200,
          crossAxisSpacing: 12,
          mainAxisSpacing: 12,
          childAspectRatio: 0.8),
      itemCount: results.length,
      itemBuilder: (context, index) {
        final r = results[index];
        final sourcePath = r['source_path'] ?? r['video_path'];
        final isVideo = (r['image_type'] ?? r['type']) == 'video';
        final thumbnailPath = r['thumbnail_path'];
        final score = r['score'] ?? 0.0;
        final timestamp = r['timestamp'] ?? 0.0;

        return InkWell(
          onTap: () => onOpenFile(sourcePath),
          child: Card(
            color: AppTheme.bgElevated,
            clipBehavior: Clip.antiAlias,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8),
              side: const BorderSide(color: AppTheme.border),
            ),
            child: Stack(
              children: [
                Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Expanded(
                      child: thumbnailPath != null
                          ? Image.file(File(thumbnailPath),
                              fit: BoxFit.cover,
                              cacheWidth: 300, 
                              errorBuilder: (c, e, s) => const Icon(Icons.broken_image))
                          : isVideo
                              ? const Icon(Icons.videocam, size: 50, color: AppTheme.textMuted)
                              : Image.file(File(sourcePath),
                                  fit: BoxFit.cover,
                                  cacheWidth: 300, 
                                  errorBuilder: (c, e, s) => const Icon(Icons.broken_image)),
                    ),
                    Container(
                      color: AppTheme.bgSurface,
                      padding: const EdgeInsets.all(8.0),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(sourcePath.split(Platform.pathSeparator).last,
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: const TextStyle(
                                  fontSize: 11,
                                  fontWeight: FontWeight.bold,
                                  color: AppTheme.textPrimary)),
                          const SizedBox(height: 4),
                          Text(isVideo ? 'Video • ${timestamp.toStringAsFixed(1)}s' : 'Hình ảnh',
                              style: const TextStyle(
                                  fontSize: 10, color: AppTheme.textSecondary)),
                        ],
                      ),
                    ),
                  ],
                ),
                if (score > 0)
                  Positioned(
                    top: 8,
                    right: 8,
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 4),
                      decoration: BoxDecoration(
                        color: AppTheme.info.withOpacity(0.9),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text('${(score * 100).toStringAsFixed(0)}%',
                          style: const TextStyle(
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                              color: AppTheme.bgBase)),
                    ),
                  ),
                if (isVideo)
                  Positioned(
                    top: 8,
                    left: 8,
                    child: Container(
                      padding: const EdgeInsets.all(4),
                      decoration: const BoxDecoration(
                        color: Colors.black54,
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(Icons.play_arrow,
                          color: Colors.white, size: 16),
                    ),
                  ),
              ],
            ),
          ),
        );
      },
    );
  }
}
