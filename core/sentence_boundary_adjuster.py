#!/usr/bin/env python3
"""
Sentence Boundary Adjuster
Ensures video clips don't cut off mid-sentence by adjusting timestamps to sentence boundaries
"""

import re
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)


class SentenceBoundaryAdjuster:
    """Adjusts clip timestamps to ensure complete sentences using WhisperX word-level timestamps"""
    
    def __init__(self):
        """Initialize the sentence boundary adjuster"""
        # Sentence ending punctuation for different languages
        self.sentence_endings = {
            'zh': ['。', '！', '？', '…', '；'],  # Chinese
            'en': ['.', '!', '?', ';'],  # English
            'ja': ['。', '！', '？', '…'],  # Japanese
            'ko': ['.', '!', '?'],  # Korean
        }
        
        # Common sentence ending patterns (language-agnostic)
        self.sentence_end_pattern = re.compile(r'[.!?。！？…；;]\s*$')
    
    def parse_srt_with_words(self, srt_path: str) -> List[Dict]:
        """Parse SRT file and extract all subtitle segments with word-level timing"""
        segments = []
        
        try:
            with open(srt_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            blocks = re.split(r'\n\s*\n', content)
            
            for block in blocks:
                lines = block.strip().split('\n')
                if len(lines) >= 3:
                    timing_match = re.match(
                        r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})',
                        lines[1]
                    )
                    if timing_match:
                        start_time = timing_match.group(1)
                        end_time = timing_match.group(2)
                        text = ' '.join(lines[2:])
                        
                        segments.append({
                            'start_time': start_time,
                            'end_time': end_time,
                            'start_seconds': self._time_to_seconds(start_time),
                            'end_seconds': self._time_to_seconds(end_time),
                            'text': text
                        })
            
            logger.info(f"📝 Parsed {len(segments)} segments from {Path(srt_path).name}")
            return segments
            
        except Exception as e:
            logger.error(f"Error parsing SRT file {srt_path}: {e}")
            return []
    
    def _time_to_seconds(self, time_str: str) -> float:
        """Convert SRT time format (HH:MM:SS,mmm) to seconds"""
        time_part, ms_part = time_str.split(',')
        h, m, s = map(int, time_part.split(':'))
        ms = int(ms_part)
        return h * 3600 + m * 60 + s + ms / 1000.0
    
    def _seconds_to_time(self, seconds: float) -> str:
        """Convert seconds to SRT time format (HH:MM:SS,mmm)"""
        ms = int((seconds % 1) * 1000)
        total_seconds = int(seconds)
        
        h = total_seconds // 3600
        m = (total_seconds % 3600) // 60
        s = total_seconds % 60
        
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
    
    def _is_sentence_boundary(self, text: str) -> bool:
        """Check if text ends with sentence-ending punctuation"""
        if not text:
            return False
        
        text = text.strip()
        
        # Check if text ends with sentence-ending punctuation
        if self.sentence_end_pattern.search(text):
            return True
        
        for lang_endings in self.sentence_endings.values():
            if any(text.endswith(ending) for ending in lang_endings):
                return True
        
        return False
    
    def _contains_sentence_boundary(self, text: str) -> bool:
        """Check if text contains sentence-ending punctuation anywhere"""
        if not text:
            return False
        
        text = text.strip()
        
        # Check if text contains any sentence-ending punctuation
        for lang_endings in self.sentence_endings.values():
            if any(ending in text for ending in lang_endings):
                return True
        
        return False

    
    def _adjust_time_to_gap(self, segments: List[Dict], time_seconds: float, time_label: str) -> Tuple[float, str]:
        """
        Adjust a time point to the nearest gap between subtitles
        
        Args:
            segments: List of subtitle segments
            time_seconds: The time to adjust
            time_label: Label for logging (e.g., "开始", "结束")
            
        Returns:
            Tuple of (adjusted_time, subtitle_text)
        """
        segment, seg_index = self._get_segment_at_time(segments, time_seconds)
        original_subtitle = self._get_subtitle_at_time(segments, time_seconds)
        
        logger.info(f"⏱️  {time_label}时间 {self._seconds_to_time(time_seconds)}: {'在字幕段内' if segment else '在字幕段之间'}")
        
        if not segment:
            # Time is between subtitles, no adjustment needed
            logger.info(f"✓ {time_label}时间已在字幕段之间，无需调整")
            return time_seconds, original_subtitle
        
        # Time is in subtitle, show content
        logger.info(f"   字幕内容: 「{segment['text'][:50]}{'...' if len(segment['text']) > 50 else ''}」")
        
        # Calculate position in segment
        segment_duration = segment['end_seconds'] - segment['start_seconds']
        time_in_segment = time_seconds - segment['start_seconds']
        progress = time_in_segment / segment_duration if segment_duration > 0 else 0
        
        logger.info(f"   时间位置: 在字幕段的 {progress*100:.1f}% 处")
        
        if progress < 0.5:
            # Near start, adjust to gap between previous and current
            logger.info(f"🔍 靠近字幕段开头，调整到上一句结尾和这一句开头之间...")
            if seg_index > 0:
                prev_seg = segments[seg_index - 1]
                gap_duration = segment['start_seconds'] - prev_seg['end_seconds']
                
                gap_time = self._find_gap_between_segments(segments, seg_index - 1, seg_index)
                if gap_time is not None:
                    subtitle = prev_seg['text'].strip()
                    if len(subtitle) > 50:
                        subtitle = subtitle[:47] + "..."
                    
                    extension = segment['start_seconds'] - gap_time
                    
                    if gap_duration > 1.0:
                        logger.info(
                            f"✓ 间隔较大({gap_duration:.2f}s)，最多提前1秒: {self._seconds_to_time(gap_time)} "
                            f"(提前 {extension:.2f}s)"
                        )
                    else:
                        logger.info(
                            f"✓ 调整到间隙中点: {self._seconds_to_time(gap_time)} "
                            f"(在 {self._seconds_to_time(prev_seg['end_seconds'])} 和 "
                            f"{self._seconds_to_time(segment['start_seconds'])} 之间)"
                        )
                    return gap_time, subtitle
                else:
                    logger.info(f"⚠️  无法找到间隙，保持原时间")
                    return time_seconds, original_subtitle
            else:
                logger.info(f"⚠️  已是第一个字幕段，保持原时间")
                return time_seconds, original_subtitle
        else:
            # Near end, adjust to gap between current and next
            logger.info(f"🔍 靠近字幕段结尾，调整到这一句结尾和下一句开头之间...")
            if seg_index < len(segments) - 1:
                next_seg = segments[seg_index + 1]
                gap_duration = next_seg['start_seconds'] - segment['end_seconds']
                
                gap_time = self._find_gap_between_segments(segments, seg_index, seg_index + 1)
                if gap_time is not None:
                    subtitle = segment['text'].strip()
                    if len(subtitle) > 50:
                        subtitle = subtitle[:47] + "..."
                    
                    extension = gap_time - segment['end_seconds']
                    
                    if gap_duration > 1.0:
                        logger.info(
                            f"✓ 间隔较大({gap_duration:.2f}s)，最多延长1秒: {self._seconds_to_time(gap_time)} "
                            f"(延长 {extension:.2f}s)"
                        )
                    else:
                        logger.info(
                            f"✓ 调整到间隙中点: {self._seconds_to_time(gap_time)} "
                            f"(在 {self._seconds_to_time(segment['end_seconds'])} 和 "
                            f"{self._seconds_to_time(next_seg['start_seconds'])} 之间)"
                        )
                    return gap_time, subtitle
                else:
                    logger.info(f"⚠️  无法找到间隙，保持原时间")
                    return time_seconds, original_subtitle
            else:
                logger.info(f"⚠️  已是最后一个字幕段，保持原时间")
                return time_seconds, original_subtitle
    
    def _find_gap_between_segments(self, segments: List[Dict], seg1_index: int, seg2_index: int, max_gap_extension: float = 1.0) -> Optional[float]:
        """Find the middle point between two segments (in the gap)
        
        Args:
            segments: List of subtitle segments
            seg1_index: Index of first segment
            seg2_index: Index of second segment
            max_gap_extension: Maximum seconds to extend into gap (default 1.0s)
        """
        if seg1_index < 0 or seg2_index >= len(segments):
            return None
        
        seg1 = segments[seg1_index]
        seg2 = segments[seg2_index]
        
        # Calculate middle point between seg1 end and seg2 start
        gap_start = seg1['end_seconds']
        gap_end = seg2['start_seconds']
        
        if gap_end <= gap_start:
            # No gap, return the boundary point
            return gap_start
        
        gap_duration = gap_end - gap_start
        
        # If gap is large (> max_gap_extension), only extend by max_gap_extension
        if gap_duration > max_gap_extension:
            return gap_start + max_gap_extension
        
        # Otherwise, use middle point
        middle = (gap_start + gap_end) / 2.0
        return middle
    
    def _get_segment_at_time(self, segments: List[Dict], time_seconds: float) -> Optional[Tuple[Dict, int]]:
        """Get the subtitle segment at a specific time and its index"""
        for i, seg in enumerate(segments):
            if seg['start_seconds'] <= time_seconds <= seg['end_seconds']:
                return seg, i
        return None, -1
    
    def _is_time_in_subtitle(self, segments: List[Dict], time_seconds: float) -> bool:
        """Check if a time point is within any subtitle segment"""
        seg, _ = self._get_segment_at_time(segments, time_seconds)
        return seg is not None
    
    def _get_subtitle_at_time(self, segments: List[Dict], time_seconds: float) -> str:
        """Get the subtitle text at a specific time"""
        for seg in segments:
            if seg['start_seconds'] <= time_seconds <= seg['end_seconds']:
                text = seg['text'].strip()
                # Truncate long text for readability
                if len(text) > 50:
                    text = text[:47] + "..."
                return text
        
        # If no exact match, find the closest segment
        closest_seg = min(segments, key=lambda s: min(
            abs(s['start_seconds'] - time_seconds),
            abs(s['end_seconds'] - time_seconds)
        ))
        text = closest_seg['text'].strip()
        if len(text) > 50:
            text = text[:47] + "..."
        return text
    
    def adjust_clip_boundaries(
        self,
        srt_path: str,
        start_time: str,
        end_time: str,
        max_extension: float = 5.0
    ) -> Tuple[str, str, bool]:
        """Adjust clip start and end times to align with sentence boundaries"""
        segments = self.parse_srt_with_words(srt_path)
        if not segments:
            logger.warning(f"No segments found in {srt_path}, returning original times")
            return start_time, end_time, False
        
        if ',' in start_time:
            start_seconds = self._time_to_seconds(start_time)
        else:
            start_seconds = self._simple_time_to_seconds(start_time)
        
        if ',' in end_time:
            end_seconds = self._time_to_seconds(end_time)
        else:
            end_seconds = self._simple_time_to_seconds(end_time)
        
        original_start = start_seconds
        original_end = end_seconds
        
        # Get original subtitle texts
        original_start_subtitle = self._get_subtitle_at_time(segments, start_seconds)
        original_end_subtitle = self._get_subtitle_at_time(segments, end_seconds)
        
        # Adjust start and end times to gaps
        adjusted_start, start_subtitle = self._adjust_time_to_gap(segments, start_seconds, "开始")
        adjusted_end, end_subtitle = self._adjust_time_to_gap(segments, end_seconds, "结束")
        
        was_adjusted = (adjusted_start != original_start) or (adjusted_end != original_end)
        
        if was_adjusted:
            start_diff = original_start - adjusted_start
            end_diff = adjusted_end - original_end
            
            original_start_time = self._seconds_to_time(original_start)
            original_end_time = self._seconds_to_time(original_end)
            adjusted_start_time = self._seconds_to_time(adjusted_start)
            adjusted_end_time = self._seconds_to_time(adjusted_end)
            
            logger.info(
                f"✂️  调整片段边界以保证句子完整性: "
                f"开始 {start_diff:+.2f}s, 结束 {end_diff:+.2f}s"
            )
            logger.info(
                f"✂️  时间调整: {original_start_time} → {adjusted_start_time} (开始), "
                f"{original_end_time} → {adjusted_end_time} (结束)"
            )
            
            # Print subtitle changes
            if adjusted_start != original_start:
                if original_start_subtitle and start_subtitle and original_start_subtitle != start_subtitle:
                    logger.info(f"📝 开始字幕: 「{original_start_subtitle}」→「{start_subtitle}」")
                elif start_subtitle:
                    logger.info(f"📝 开始字幕: 「{start_subtitle}」")
                    
            if adjusted_end != original_end:
                if original_end_subtitle and end_subtitle and original_end_subtitle != end_subtitle:
                    logger.info(f"📝 结束字幕: 「{original_end_subtitle}」→「{end_subtitle}」")
                elif end_subtitle:
                    logger.info(f"📝 结束字幕: 「{end_subtitle}」")
        else:
            logger.info("✓ 片段边界已对齐句子边界")
        
        adjusted_start_time = self._seconds_to_time(adjusted_start)
        adjusted_end_time = self._seconds_to_time(adjusted_end)
        
        return adjusted_start_time, adjusted_end_time, was_adjusted
    
    def _simple_time_to_seconds(self, time_str: str) -> float:
        """Convert simple time format (MM:SS or HH:MM:SS) to seconds"""
        parts = time_str.split(':')
        if len(parts) == 2:
            m, s = map(int, parts)
            return m * 60 + s
        elif len(parts) == 3:
            h, m, s = map(int, parts)
            return h * 3600 + m * 60 + s
        else:
            raise ValueError(f"Invalid time format: {time_str}")
    
    def adjust_moments_in_analysis(
        self,
        analysis_data: Dict,
        srt_dir: Path,
        max_extension: float = 5.0
    ) -> Dict:
        """Adjust all engaging moments in analysis data to align with sentence boundaries"""
        if 'top_engaging_moments' not in analysis_data:
            logger.warning("No top_engaging_moments found in analysis data")
            return analysis_data
        
        adjusted_count = 0
        
        for moment in analysis_data['top_engaging_moments']:
            timing = moment.get('timing', {})
            video_part = timing.get('video_part', '')
            start_time = timing.get('start_time', '')
            end_time = timing.get('end_time', '')
            
            if not all([video_part, start_time, end_time]):
                logger.warning(f"Missing timing info for moment: {moment.get('title', 'Unknown')}")
                continue
            
            srt_path = srt_dir / f"{video_part}.srt"
            if not srt_path.exists():
                logger.warning(f"SRT file not found: {srt_path}")
                continue
            
            adjusted_start, adjusted_end, was_adjusted = self.adjust_clip_boundaries(
                str(srt_path), start_time, end_time, max_extension
            )
            
            if was_adjusted:
                timing['start_time'] = adjusted_start
                timing['end_time'] = adjusted_end
                
                start_sec = self._time_to_seconds(adjusted_start)
                end_sec = self._time_to_seconds(adjusted_end)
                timing['duration'] = int(end_sec - start_sec)
                
                adjusted_count += 1
                logger.info(f"✓ Adjusted moment: {moment.get('title', 'Unknown')}")
        
        if adjusted_count > 0:
            logger.info(f"🎯 Adjusted {adjusted_count}/{len(analysis_data['top_engaging_moments'])} moments")
        else:
            logger.info("✓ All moments already have complete sentences")
        
        return analysis_data
